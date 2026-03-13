from django import forms
from .models import WorkingHours 
from .models import BookingService, Provider
from django.utils.translation import gettext_lazy as _


from django import forms
from .models import BookingService, Provider

class BookingServiceForm(forms.ModelForm):
    # Используем чекбоксы вместо выпадающего списка
    providers = forms.ModelMultipleChoiceField(
        queryset=Provider.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Select providers who can perform this service. Leave unselected if anyone can do this.")
    )

    class Meta:
        model = BookingService
        fields = ['title', 'description', 'price', 'booking_type', 'providers', 'is_active', 'image']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'pixel-input'}),
            'description': forms.Textarea(attrs={'class': 'pixel-input', 'rows': 5}),
            'price': forms.NumberInput(attrs={
                'class': 'pixel-input',
                'placeholder': 'Leave empty if price is not fixed'
            }),
            'booking_type': forms.Select(attrs={'class': 'pixel-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'pixel-checkbox'}),
            'image': forms.ClearableFileInput(attrs={'class': 'pixel-file-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BookingServiceForm, self).__init__(*args, **kwargs)
        
        if user:
            # Загружаем только исполнителей текущего пользователя
            user_providers = Provider.objects.filter(owner=user)
            self.fields['providers'].queryset = user_providers
            
            # Если исполнителей нет, меняем текст подсказки
            if not user_providers.exists():
                self.fields['providers'].help_text = _("No providers yet. Please Add Providers first.")


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