# profile_app/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from PIL import Image
import os
# Импортируем функцию slugify для преобразования обычного текста в URL-безопасный формат
from django.utils.text import slugify

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug")
    is_email_verified = models.BooleanField(default=False)
    sku_limit = models.PositiveIntegerField(default=10, verbose_name="SKU Limit")
    show_in_catalog = models.BooleanField(default=False, verbose_name="Show in Catalog")
    
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_seller(self):
        return self.groups.filter(name='Seller').exists()

    @property
    def is_blogger(self):
        return self.groups.filter(name='Blogger').exists()

    @property
    def is_gallery_owner(self):
        return self.groups.filter(name='Photographer').exists()

    def save(self, *args, **kwargs):
        # Шаг 0: Автоматическая генерация слага, если он пустой (срабатывает для новых пользователей)
        if not self.slug:
            # Превращаем имя пользователя в базовый слаг (например, "My Name" станет "my-name")
            base_slug = slugify(self.username)
            self.slug = base_slug
            counter = 1
            
            # Цикл проверяет базу данных на наличие дубликатов. 
            # Если такой слаг уже кем-то занят, добавляем к нему цифру (например, "my-name-1"), 
            # пока не найдем полностью уникальный вариант.
            while CustomUser.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        # Шаг 1: Проверка и физическое удаление старого аватара (твой существующий код)
        if self.pk:
            try:
                old_user = CustomUser.objects.get(pk=self.pk)
                if old_user.avatar and old_user.avatar != self.avatar:
                    if os.path.isfile(old_user.avatar.path):
                        os.remove(old_user.avatar.path)
            except CustomUser.DoesNotExist:
                pass

        # Шаг 2: Стандартное сохранение в базу данных
        super().save(*args, **kwargs)

        # Шаг 3: Обрезка и оптимизация нового аватара (твой существующий код)
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.width != 100 or img.height != 100:
                min_dim = min(img.width, img.height)
                left = (img.width - min_dim) / 2
                top = (img.height - min_dim) / 2
                right = (img.width + min_dim) / 2
                bottom = (img.height + min_dim) / 2
                
                img = img.crop((left, top, right, bottom))
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                img.save(self.avatar.path, format='JPEG', quality=85, optimize=True)