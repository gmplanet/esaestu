from django import forms
from .models import WorkingHours 
from .models import BookingService, Provider

# Форма для создания и редактирования услуги
class BookingServiceForm(forms.ModelForm):
    class Meta:
        model = BookingService
        # Добавляем 'image' в список полей, которые пользователь будет заполнять
        fields = ['title', 'description', 'price', 'is_active', 'image']
        
        # Применяем CSS-стили напрямую к HTML-элементам формы
        widgets = {
            'title': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'description': forms.Textarea(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;', 'rows': 5}),
            'price': forms.NumberInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'margin-bottom: 10px;'}),
            # Добавляем виджет загрузки файла с пиксельным шрифтом
            'image': forms.ClearableFileInput(attrs={'style': 'margin-bottom: 10px; font-family: "VT323", monospace; font-size: 1.2rem;'}),
        }

# Форма для добавления и редактирования исполнителя
class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        # Добавляем 'avatar' в список полей
        fields = ['name', 'is_active', 'avatar']
        
        # Настраиваем внешний вид полей ввода
        widgets = {
            'name': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'margin-bottom: 10px;'}),
            # Добавляем виджет загрузки фото исполнителя с пиксельным шрифтом
            'avatar': forms.ClearableFileInput(attrs={'style': 'margin-bottom: 10px; font-family: "VT323", monospace; font-size: 1.2rem;'}),
        }

class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ['start_time', 'end_time', 'is_day_off']
        
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'style': 'padding: 5px; font-family: "VT323", monospace; font-size: 1.2rem;'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'style': 'padding: 5px; font-family: "VT323", monospace; font-size: 1.2rem;'}),
            'is_day_off': forms.CheckboxInput(attrs={'style': 'transform: scale(1.5); margin-left: 10px;'}),
        }