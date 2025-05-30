from django.shortcuts import render, get_object_or_404

# Коллекция данных (имитация БД)
services = [
    {"id": 1, "name": "Фишинг", "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSJ-AYLqLiLPyQ5MlVWl9R7WTQogw3cNFXF1A&s", "description": "Кража данных"},
    {"id": 2, "name": "Трояны", "image": "https://cdn-icons-png.flaticon.com/512/554/554268.png", "description": "Вирусы и трояны"},
    {"id": 3, "name": "Майнеры", "image": "https://www.ferra.ru/imgs/2018/11/23/17/2460314/6ae806c5d12062cf0aa4364f63a3d1322c8198b6.jpg", "description": "Вредоносный код использует мощность вашего ПК с целью добычи криптовалюты"},
    {"id": 4, "name": "DDoS-атака", "image": "https://selectel.ru/blog/wp-content/uploads/2020/09/PR-14317_3.png", "description": "Атака на сервер"},
]

def index(request):
    return render(request, "index.html", {"services": services})

def service(request):
    query = request.GET.get("query", "").strip().lower()
    filtered_services = [s for s in services if query in s["name"].lower()] if query else services
    return render(request, "service.html", {"service": filtered_services, "query": query})

def service_detail(request, service_id):
    service = get_object_or_404(services, id=service_id)
    return render(request, "service_detail.html", {"service": service})

def application(request):
    return render(request, "applications.html" )