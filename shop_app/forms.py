from django import forms
from django.utils.html import strip_tags # Инструмент для вырезания HTML-тегов
from django.core.exceptions import ValidationError # Инструмент для вывода ошибок валидации
import re # Библиотека для работы с регулярными выражениями
from .models import Product, Order

# Создаем класс формы на основе нашей модели базы данных Product
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'stock', 'is_active']
        
        widgets = {
            'title': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'description': forms.Textarea(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'rows': 5}),
            'price': forms.NumberInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'stock': forms.NumberInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'margin-bottom: 10px;'}),
        }

# ==========================================
# НОВАЯ ФОРМА ОФОРМЛЕНИЯ ЗАКАЗА
# ==========================================
class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_email', 'additional_info']
        
        widgets = {
            'customer_name': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            # pattern заставляет браузер проверять ввод перед отправкой
            # title показывает подсказку, если ввод неверный
            'customer_phone': forms.TextInput(attrs={
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 
                'required': True,
                'pattern': r'^\+?[0-9]{7,15}$',
                'title': 'Введите номер телефона (только цифры, можно начать с +)'
            }),
            'customer_email': forms.EmailInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            'additional_info': forms.Textarea(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'rows': 4, 'maxlength': '500'}),
        }

    # Серверная проверка телефона (на случай, если защиту браузера отключили)
    # Метод, начинающийся с clean_, автоматически вызывается Django при проверке формы
    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')
        # Проверяем строку на соответствие правилу: опциональный + и от 7 до 15 цифр
        if not re.match(r'^\+?[0-9]{7,15}$', phone):
            raise ValidationError('Номер телефона должен содержать только цифры.')
        return phone

    # Серверная защита комментария от внедрения вредоносного кода (XSS)
    def clean_additional_info(self):
        info = self.cleaned_data.get('additional_info')
        if info:
            # strip_tags удаляет любые HTML-теги (например, <script>alert(1)</script> превратится в alert(1))
            info = strip_tags(info)
        return info