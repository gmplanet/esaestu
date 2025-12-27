from django.shortcuts import render
from .models import Maintenance

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пропускаем админку
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # 2. Получаем объект модели Maintenance (просто Maintenance, как в models.py)
        maintenance = Maintenance.objects.first()

        # 3. Проверяем поле is_active
        if maintenance and maintenance.is_active:
            # Передаем весь объект в шаблон, чтобы можно было вывести сообщение
            return render(request, 'maintenance.html', {'maintenance': maintenance})

        return self.get_response(request)