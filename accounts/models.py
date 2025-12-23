from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True) # Теперь база не примет дубликат
    is_email_verified = models.BooleanField(default=False)
    
    # Это поможет Django понять, что email теперь важен
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']