from django.contrib.auth.models import AbstractUser
from django.db import models
from allauth.account.signals import email_confirmed, user_signed_up # Импортируем оба отсюда
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

class CustomUser(AbstractUser):
    # 1. Email — обязательный и уникальный (наш главный логин)
    email = models.EmailField(unique=True)
    
    # 2. Никнейм — обязательный и уникальный (как ты и просил)
    # Мы оставляем стандартный username, но убеждаемся, что он не пустой
    username = models.CharField(max_length=150, unique=True)
    
    is_email_verified = models.BooleanField(default=False)

    # 3. ГЛАВНОЕ: Указываем Django использовать email для входа
    USERNAME_FIELD = 'email'
    
    # 4. ГЛАВНОЕ: Указываем, что при регистрации (в консоли) 
    # НУЖНО спрашивать username, но НЕ НУЖНО спрашивать Имя и Фамилию
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    



# 1. Для обычной регистрации (уже работает)
@receiver(email_confirmed)
def update_user_email_verified(request, email_address, **kwargs):
    user = email_address.user
    user.is_email_verified = True
    user.save()

# 2. Для регистрации через Google (и другие соцсети)
@receiver(user_signed_up)
def set_verified_on_signup(request, user, **kwargs):
    # Если пользователь пришел через соцсеть, сразу подтверждаем
    if hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists():
        user.is_email_verified = True
        user.save()

# 3. Для привязки соцсети к уже существующему аккаунту
@receiver(social_account_added)
def update_user_social_verified(request, socialaccount, **kwargs):
    user = socialaccount.user
    user.is_email_verified = True
    user.save()