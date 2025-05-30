from rest_framework import viewsets
from .models import Service, Application, ApplicationService
from .serializers import ServiceSerializer, ApplicationSerializer, ApplicationServiceSerializer
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied

# Фильтр для услуг
class ServiceFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='icontains')  # Поиск по части имени услуги

    class Meta:
        model = Service
        fields = ['name']

# ViewSet для управления услугами
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_deleted=False)
    serializer_class = ServiceSerializer
    filter_class = ServiceFilter  # Применяем фильтрацию для услуг

# ViewSet для управления заявками
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.filter(is_deleted=False)
    serializer_class = ApplicationSerializer

# ViewSet для управления связью заявки и услуги
class ApplicationServiceViewSet(viewsets.ModelViewSet):
    queryset = ApplicationService.objects.all()
    serializer_class = ApplicationServiceSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to perform this action.")

        # Находим черновик заявки для текущего пользователя
        draft_application = Application.objects.filter(user=user, status='draft', is_deleted=False).first()
        if not draft_application:
            raise PermissionDenied("You must have a draft application to add services.")

        # Сохраняем связь между заявкой и услугой
        serializer.save(application=draft_application)

    def perform_destroy(self, instance):
        instance.delete()
