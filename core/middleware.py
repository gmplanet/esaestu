from django.shortcuts import render
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Сразу пропускаем админку
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # 2. Безопасно берем запись из базы
        try:
            maintenance = Maintenance.objects.first()
        except Exception:
            # Если база данных недоступна, просто работаем дальше
            return self.get_response(request)

        # 3. Если запись есть и режим активен
        if maintenance and maintenance.is_active:
            # Используем самый простой render
            return render(request, 'maintenance.html', {'maintenance': maintenance})

        return self.get_response(request)