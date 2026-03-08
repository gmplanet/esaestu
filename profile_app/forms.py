# profile_app/forms.py
from allauth.account.forms import SignupForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms
# Импортируем функцию для получения активной модели пользователя
from django.contrib.auth import get_user_model

# Инициализируем модель пользователя
User = get_user_model()

# Твоя существующая форма регистрации (остается без изменений)
class CustomSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(), label='Captcha')

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['email'].placeholder = 'example@mail.com'
        self.fields['username'].placeholder = 'YourNickname'

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        return user

# Наша новая форма для настроек профиля (аватар и чекбокс)
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        # Разрешаем пользователю менять только эти два поля
        fields = ['avatar', 'show_in_catalog']