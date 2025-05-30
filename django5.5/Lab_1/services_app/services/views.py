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
        
        queryset = self.filter_class(request.GET, queryset=self.get_queryset()).qs
        serializer = ServiceSerializer(queryset, many=True, context={'request': request})
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
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can update services")
            
        service = self.get_queryset().filter(pk=pk).first()
        if not service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ServiceSerializer(service, data=request.data, context={'request': request}, partial=True)
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
    
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Application.objects.none()  # Вернёт пустой queryset

        if user.is_staff:
            return Application.objects.filter(is_deleted=False)

        return Application.objects.filter(user=user, is_deleted=False)

    # def get_queryset(self):
    #     user = self.request.user
    #     if not user.is_authenticated:
    #         return Application.objects.none()
    #     if user.is_staff:
    #         return Application.objects.filter(is_deleted=False)
    #     return Application.objects.filter(user=user, is_deleted=False)
    
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
        serializer = ApplicationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if application.status == 'draft':
            if request.user != application.user:
                return Response({"detail": "You can only edit your own drafts."}, 
                              status=status.HTTP_403_FORBIDDEN)
        elif application.status == 'formatted':
            if not request.user.is_staff or request.user != application.moderator:
                return Response({"detail": "Only assigned moderator can change formatted applications."}, 
                              status=status.HTTP_403_FORBIDDEN)
        
        serializer = ApplicationSerializer(application, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user != application.user and not request.user.is_staff:
            return Response({"detail": "You can't delete this application."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        application.is_deleted = True
        application.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []