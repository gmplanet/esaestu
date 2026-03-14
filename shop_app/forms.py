# shop_app/forms.py
from django import forms
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
import re
from .models import Product, Order

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'stock', 'is_active']
        
        widgets = {
            'title': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'description': forms.Textarea(attrs={
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 
                'rows': 8, 
                'placeholder': 'Подробное описание товара...'
            }),
            'price': forms.NumberInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'stock': forms.NumberInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'margin-bottom: 10px;'}),
        }

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_email', 'additional_info']
        
        widgets = {
            'customer_name': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            'customer_phone': forms.TextInput(attrs={
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 
                'required': True,
                'pattern': r'^\+?[0-9]{7,15}$',
                'title': 'Введите номер телефона (только цифры, можно начать с +)'
            }),
            'customer_email': forms.EmailInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'required': True}),
            'additional_info': forms.Textarea(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'rows': 4, 'maxlength': '500'}),
        }

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')
        if not re.match(r'^\+?[0-9]{7,15}$', phone):
            raise ValidationError('Номер телефона должен содержать только цифры.')
        return phone

    def clean_additional_info(self):
        info = self.cleaned_data.get('additional_info')
        if info:
            info = strip_tags(info)
        return info