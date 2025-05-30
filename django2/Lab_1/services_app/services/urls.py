from django.urls import path
from .views import index, service, service_detail, application

urlpatterns = [
    path("", index, name="index"),
    path("service/", service, name="services"),
    path("applications/", application, name="appli"),
    path("services/<int:service_id>/", service_detail, name="service_detail"),
]
