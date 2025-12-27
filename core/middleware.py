from django.shortcuts import render
from django.template.loader import get_template
from django.http import HttpResponse
from django.utils.translation import get_language
from .models import Maintenance

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        maintenance = Maintenance.objects.first()

        if maintenance and maintenance.is_active:
            # Используем get_template + render без контекста запроса,
            # чтобы пропустить выполнение context_processors
            template = get_template('maintenance.html')
            html = template.render({'content': maintenance.message})
            return HttpResponse(html, status=503) # 503 Service Unavailable

        return self.get_response(request)