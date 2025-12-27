from django.shortcuts import render
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пропускаем админку, чтобы не заблокировать вход
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # 2. Получаем настройки режима обслуживания
        try:
            maintenance = Maintenance.objects.first()
        except Exception:
            # Если база еще не мигрирована или ошибка в БД, пропускаем запрос
            return self.get_response(request)

        # 3. Если режим включен в админке
        if maintenance and maintenance.is_active:
            # Используем стандартный render. 
            # Он сам найдет maintenance.html в корневой папке templates,
            # так как она прописана в DIRS вашего settings.py
            return render(
                request, 
                'maintenance.html', 
                {'content': maintenance.message},
                status=503
            )

        return self.get_response(request)