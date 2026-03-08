# profile_app/urls.py
from django.urls import path
from . import views


urlpatterns = [
    # Маршрут закрытого личного кабинета
    path('cabinet/', views.cabinet_view, name='cabinet'),
    # Маршрут публичной страницы, чтобы избежать конфликтов с основными страницами сайта
    path('u/<slug:slug>/', views.public_profile_view, name='public_profile'),
]

