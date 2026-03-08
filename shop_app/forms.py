# shop_app/forms.py
from django import forms
# Обязательно импортируем новую модель Order
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
        # Выводим только те поля, которые покупатель заполняет вручную
        fields = ['customer_name', 'customer_phone', 'customer_email', 'additional_info']
        
        widgets = {
            'customer_name': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            'customer_phone': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            'customer_email': forms.EmailInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            # Ограничиваем длину ввода до 500 символов прямо в HTML-атрибутах виджета
            'additional_info': forms.Textarea(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'rows': 4, 'maxlength': '500'}),
        }