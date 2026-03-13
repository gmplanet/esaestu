# profile_app/forms.py
from allauth.account.forms import SignupForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(), label='Captcha')
    
    # Добавляем поле выбора валюты при регистрации
    currency = forms.ChoiceField(
        choices=User.CURRENCY_CHOICES,
        initial='EUR',
        widget=forms.Select(attrs={'class': 'pixel-input'})
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['email'].placeholder = 'example@mail.com'
        self.fields['username'].placeholder = 'YourNickname'

    def save(self, request):
        # Вызываем стандартное сохранение пользователя
        user = super(CustomSignupForm, self).save(request)
        
        # Извлекаем выбранную валюту из очищенных данных формы
        # и записываем ее в профиль нового пользователя
        user.currency = self.cleaned_data.get('currency')
        user.save()
        
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'show_in_catalog', 'currency']
        
        # Используем только CSS-классы
        widgets = {
            'currency': forms.Select(attrs={'class': 'pixel-input'}),
            'show_in_catalog': forms.CheckboxInput(attrs={'class': 'pixel-checkbox'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'pixel-file-input'}),
        }