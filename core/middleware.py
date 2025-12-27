from django.shortcuts import render
from django.utils.translation import get_language # Добавляем этот импорт
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пропускаем админку
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # 2. Пытаемся получить настройки
        maintenance = Maintenance.objects.first()

        # 3. Если режим активен
        if maintenance and maintenance.is_active:
            # Используем свойство .message, которое само выберет язык
            # благодаря тому, что мы импортировали поддержку перевода
            return render(request, 'maintenance.html', {
                'content': maintenance.message # Передаем уже готовый текст по языку
            })

        return self.get_response(request)