from allauth.account.forms import SignupForm
from captcha.fields import CaptchaField
from django import forms

class CustomSignupForm(SignupForm):
    # Добавляем капчу
    captcha = CaptchaField(label='Captcha')

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Убираем стандартные placeholders, если хочешь полный контроль в HTML
        self.fields['email'].placeholder = 'example@mail.com'
        self.fields['username'].placeholder = 'YourNickname'

    def save(self, request):
        # Вызываем базовый метод сохранения Allauth
        user = super(CustomSignupForm, self).save(request)
        # Здесь можно добавить свою логику, если нужно
        return user