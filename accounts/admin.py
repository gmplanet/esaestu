from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Добавляем наше новое поле в список отображения в админке
    list_display = ['username', 'email', 'is_email_verified', 'is_staff']
    # Добавляем поле в форму редактирования пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('is_email_verified',)}),
    )