from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from captcha.fields import CaptchaField

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # Добавляем поле капчи прямо в форму
    captcha = CaptchaField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email") # Добавляем email как обязательное поле