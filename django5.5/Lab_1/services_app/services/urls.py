from django.urls import path
from .views import (
    ServiceAPIView,
    ApplicationAPIView,
    ApplicationServiceAPIView,
    RegisterAPIView,
    UserAPIView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView



urlpatterns = [
    # API для услуг
    path('api/services/', ServiceAPIView.as_view(), name='service-list'),
    path('api/services/<int:pk>/', ServiceAPIView.as_view(), name='service-detail'),
    
    # API для заявок
    path('api/applications/', ApplicationAPIView.as_view(), name='application-list'),
    path('api/applications/<int:pk>/', ApplicationAPIView.as_view(), name='application-detail'),
    
    # API для связи заявок и услуг
    path('api/application-services/', ApplicationServiceAPIView.as_view(), name='application-service-list'),
    path('api/application-services/<int:pk>/', ApplicationServiceAPIView.as_view(), name='application-service-detail'),
    
    # API для пользователей
    path('api/users/', UserAPIView.as_view(), name='user-list'),
    path('api/users/<int:pk>/', UserAPIView.as_view(), name='user-detail'),
    path('api/register/', RegisterAPIView.as_view(), name='register'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]