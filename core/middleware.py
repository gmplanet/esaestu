from django.shortcuts import render
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем админку
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Берем настройки. Если базы нет или она пуста - просто идем дальше
        try:
            maintenance = Maintenance.objects.first()
        except:
            return self.get_response(request)

        # Если запись есть и режим активен
        if maintenance and maintenance.is_active:
            # Важно: передаем объект под именем 'maintenance'
            return render(request, 'maintenance.html', {'maintenance': maintenance})

        return self.get_response(request)