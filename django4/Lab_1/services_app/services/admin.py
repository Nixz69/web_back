from django.contrib import admin
from .models import Service, Application, User  # и ApplicationService, если есть

admin.site.register(Service)
admin.site.register(Application)
admin.site.register(User)
