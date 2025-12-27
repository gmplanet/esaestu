from django.shortcuts import render
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем админку
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Берем настройки из базы
        maintenance = Maintenance.objects.first()

        # Если режим включен, показываем заглушку
        if maintenance and maintenance.is_active:
            # Передаем объект как 'maintenance', чтобы в HTML работало {{ maintenance.message }}
            return render(request, 'maintenance.html', {'maintenance': maintenance})

        return self.get_response(request)