# profile_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Создаем класс настроек отображения пользователя в админке
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # Расширяем стандартные секции (fieldsets) новыми блоками
    # Оставляем твой блок 'Shop Settings' и добавляем новый блок 'Booking Limits' для контроля лимитов
    fieldsets = UserAdmin.fieldsets + (
        ('Shop Settings', {'fields': ('avatar', 'sku_limit', 'show_in_catalog')}),
        ('Booking Limits', {'fields': ('max_services', 'max_providers')}),
    )
    
    # Добавляем вывод новых полей лимитов в общую таблицу пользователей
    # Это позволит администратору видеть текущие ограничения сразу в общем списке
    list_display = UserAdmin.list_display + ('max_services', 'max_providers')

# Регистрируем нашу модель с новыми настройками
admin.site.register(CustomUser, CustomUserAdmin)