from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Service, Application, ApplicationService, User
from .serializers import ServiceSerializer, ApplicationSerializer, ApplicationServiceSerializer, UserSerializer
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied

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
        serializer = ServiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        service = self.get_queryset().filter(pk=pk).first()
        if not service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ServiceSerializer(service, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        service = self.get_queryset().filter(pk=pk).first()
        if not service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        service.is_deleted = True
        service.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# APIView для управления заявками
class ApplicationAPIView(APIView):
    def get_queryset(self):
        return Application.objects.filter(is_deleted=False)
    
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if application.status == 'draft' and 'status' in request.data:
            serializer = ApplicationSerializer(application, data=request.data, context={'request': request})
        elif application.status == 'formatted' and 'status' in request.data:
            if request.user == application.moderator:
                serializer = ApplicationSerializer(application, data=request.data, context={'request': request})
            else:
                return Response({"detail": "You don't have permission to change the status."}, 
                              status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Invalid status change."}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        application = self.get_queryset().filter(pk=pk).first()
        if not application:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        application.is_deleted = True
        application.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# APIView для управления связью заявки и услуги
class ApplicationServiceAPIView(APIView):
    def get_queryset(self):
        return ApplicationService.objects.all()
    
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        app_service = self.get_queryset().filter(pk=pk).first()
        if not app_service:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ApplicationServiceSerializer(app_service, data=request.data, context={'request': request})
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
    
    def post(self, request):
        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        user = self.get_queryset().filter(pk=pk).first()
        if not user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        user = self.get_queryset().filter(pk=pk).first()
        if not user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)