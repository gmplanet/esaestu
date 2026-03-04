from allauth.account.forms import SignupForm
# Импортируем поле reCAPTCHA и виджет для визуального чекбокса "Я не робот" (V2)
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms

class CustomSignupForm(SignupForm):
    # Инициализируем поле reCAPTCHA
    # Параметр widget определяет внешний вид капчи на странице
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(), label='Captcha')

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Убираем стандартные placeholders, если нужен полный контроль в HTML
        self.fields['email'].placeholder = 'example@mail.com'
        self.fields['username'].placeholder = 'YourNickname'

    def save(self, request):
        # Вызываем базовый метод сохранения Allauth
        user = super(CustomSignupForm, self).save(request)
        # Здесь можно добавить свою логику, если нужно
        return user