# profile_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Создаем класс настроек отображения пользователя в админке
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Добавляем новую секцию "Shop Settings" с нашим полем sku_limit к стандартным полям Django
    fieldsets = UserAdmin.fieldsets + (
        ('Shop Settings', {'fields': ('avatar', 'sku_limit', 'show_in_catalog')}),
    )

# Регистрируем нашу модель с новыми настройками
admin.site.register(CustomUser, CustomUserAdmin)