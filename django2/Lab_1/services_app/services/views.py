from django.shortcuts import render, get_object_or_404
from .models import Service

def index(request):
    services = Service.objects.filter(is_deleted=False)
    return render(request, "index.html", {"services": services})

def service(request):
    query = request.GET.get("query", "").strip().lower()
    services = Service.objects.filter(is_deleted=False)
    if query:
        services = services.filter(name__icontains=query)
    return render(request, "service.html", {"service": services, "query": query})

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_deleted=False)
    return render(request, "service_detail.html", {"service": service})

def application(request):
    return render(request, "applications.html")
