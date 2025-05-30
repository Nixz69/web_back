from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, ApplicationViewSet, ApplicationServiceViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'application-services', ApplicationServiceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
