from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Service, Application, ApplicationService, User
from .serializers import ServiceSerializer, ApplicationSerializer, ApplicationServiceSerializer, UserSerializer, RegisterSerializer
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
from django.core.cache import cache
import json

# Фильтр для услуг
class ServiceFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Service
        fields = ['name']

# APIView для управления услугами
class ServiceAPIView(APIView):

    filter_class = ServiceFilter
    
    def get_queryset(self):
        return Service.objects.filter(is_deleted=False)
    
    def get(self, request, pk=None):
        if pk:
            service = self.get_queryset().filter(pk=pk).first()
            if not service:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ServiceSerializer(service, context={'request': request})
            return Response(serializer.data)
        
        # Создаём ключ для кэша на основе GET-параметров
        params = request.GET.urlencode()
        cache_key = f"service_list_{params}"
        cached_json = cache.get(cache_key)
        
        if cached_json:
            data = json.loads(cached_json)
            return Response(data)

        queryset = self.filter_class(request.GET, queryset=self.get_queryset()).qs
        serializer = ServiceSerializer(queryset, many=True, context={'request': request})
        
        # Сохраняем результат в Redis на 5 минут (300 секунд)
        cache.set(cache_key, json.dumps(serializer.data), timeout=300)
        return Response(serializer.data)
    
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can create services")
            
        serializer = ServiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Для модераторов разрешаем изменение любого статуса
        if request.user.is_staff:
            serializer = ApplicationSerializer(
                application, 
                data=request.data, 
                context={'request': request}, 
                partial=True
            )
            if serializer.is_valid():
                # Автоматически назначаем модератора при первом изменении
                if not application.moderator and 'status' in request.data:
                    serializer.save(moderator=request.user)
                else:
                    serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Для обычных пользователей оставляем текущие проверки
        if application.status == 'draft':
            if request.user != application.user:
                return Response({"detail": "You can only edit your own drafts."}, 
                            status=status.HTTP_403_FORBIDDEN)
        elif application.status == 'formatted':
            if request.user != application.moderator:
                return Response({"detail": "Only assigned moderator can change formatted applications."}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        serializer = ApplicationSerializer(
            application, 
            data=request.data, 
            context={'request': request}, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can delete services")
            
        service = self.get_queryset().filter(pk=pk).first()
        if not service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        service.is_deleted = True
        service.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# APIView для управления заявками
class ApplicationAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Добавляем глобальную проверку аутентификации
    
    def get_queryset(self):
        """
        Оптимизированный queryset с select_related для user и moderator
        """
        queryset = Application.objects.filter(is_deleted=False)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        return queryset.select_related('user', 'moderator')
    
    def get(self, request, pk=None):
        if pk:
            application = self.get_queryset().filter(pk=pk).first()
            if not application:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ApplicationSerializer(application, context={'request': request})
            return Response(serializer.data)
        
        serializer = ApplicationSerializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ApplicationSerializer(
            data=request.data, 
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def put(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Разрешаем модераторам изменять статус
        if request.user.is_staff:
            serializer = ApplicationSerializer(
                application, 
                data=request.data, 
                context={'request': request}, 
                partial=True
            )
            if serializer.is_valid():
                # Сохраняем модератора при первом изменении
                if not application.moderator and 'status' in request.data:
                    serializer.save(moderator=request.user)
                else:
                    serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {"detail": "You don't have permission to edit this application."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    def delete(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response(
                {"detail": "Not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.user != application.user and not request.user.is_staff:
            return Response(
                {"detail": "You can't delete this application."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        application.is_deleted = True
        application.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    
    def _check_application_permissions(self, user, application):
        """
        Вспомогательный метод для проверки прав доступа к заявке
        """
        if user.is_staff:
            return True
            
        if application.status == 'draft':
            return user == application.user
            
        if application.status == 'formatted':
            return user == application.moderator
            
        return False

# APIView для управления связью заявки и услуги
class ApplicationServiceAPIView(APIView):
    
    def get_queryset(self):
        return ApplicationService.objects.filter(application__user=self.request.user)
    
    def get(self, request, pk=None):
        if pk:
            app_service = self.get_queryset().filter(pk=pk).first()
            if not app_service:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ApplicationServiceSerializer(app_service, context={'request': request})
            return Response(serializer.data)
        
        serializer = ApplicationServiceSerializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ApplicationServiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            application = serializer.validated_data['application']
            if application.user != request.user:
                return Response({"detail": "You can't add services to this application."}, 
                              status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        app_service = self.get_queryset().filter(pk=pk).first()
        if not app_service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if app_service.application.user != request.user:
            return Response({"detail": "You can't edit this application service."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = ApplicationServiceSerializer(app_service, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            if 'quantity' in request.data:
                instance.quantity = request.data['quantity']
                instance.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        app_service = self.get_queryset().filter(pk=pk).first()
        if not app_service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if app_service.application.user != request.user:
            return Response({"detail": "You can't delete this application service."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        app_service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# APIView для управления пользователями
class UserAPIView(APIView):
    def get_queryset(self):
        return User.objects.all()
    
    def get(self, request, pk=None):
        if pk:
            user = self.get_queryset().filter(pk=pk).first()
            if not user:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)
        
        serializer = UserSerializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            # Проверка прав (только админ или сам пользователь может удалить)
            if not request.user.is_staff and request.user.id != user.id:
                return Response({"detail": "You don't have permission to delete this user."}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

class AdminCheckView(APIView):
    def get(self, request):
        return Response({
            'is_admin': request.user.is_staff or request.user.is_superuser
        }, status=status.HTTP_200_OK)

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
        })