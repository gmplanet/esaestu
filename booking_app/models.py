import os
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.validators import validate_is_image
import uuid
import string
import secrets
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile



class Provider(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='providers',
        verbose_name=_("Owner")
    )
    name = models.CharField(_("Name"), max_length=100)
    is_active = models.BooleanField(_("Active"), default=True)
    avatar = models.ImageField(
        upload_to='providers/', 
        blank=True, 
        null=True, 
        verbose_name=_("Provider Avatar"),
        validators=[validate_is_image] # Исправлено: валидатор теперь внутри ImageField
    )
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"

    def save(self, *args, **kwargs):
        if self.avatar:
            # Открываем изображение
            img = Image.open(self.avatar)
            
            # ImageOps.fit вырезает квадрат из центра и ресайзит до 100x100
            # Это удалит всё лишнее по бокам или сверху/снизу автоматически
            img = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            # Пытаемся сохранить оригинальный формат или используем JPEG
            img_format = img.format if img.format else 'JPEG'
            img.save(buffer, format=img_format, quality=85)
            
            file_name = os.path.basename(self.avatar.name)
            self.avatar.save(file_name, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)    


class BookingService(models.Model):
    # Обновляем описание для точного времени
    BOOKING_TYPE_CHOICES = [
        ('slots', _('15-minute Slots')),
        ('exact_time', _('Exact Time (Start and End)')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='booking_services',
        verbose_name=_("Owner")
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, null=True, blank=True)
    booking_type = models.CharField(
        _("Booking Type"),
        max_length=20,
        choices=BOOKING_TYPE_CHOICES,
        default='slots'
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to='booking_services/', 
        blank=True, 
        null=True, 
        verbose_name=_("Service Image"), 
        validators=[validate_is_image]
    )

    # НОВОЕ ПОЛЕ: Связь с исполнителями
    providers = models.ManyToManyField(
        Provider,
        blank=True,
        related_name='services',
        verbose_name=_("Providers")
    )

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            
            # Применяем тот же агрессивный кроп 100x100
            img = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            img_format = img.format if img.format else 'JPEG'
            img.save(buffer, format=img_format, quality=85)
            
            file_name = os.path.basename(self.image.name)
            self.image.save(file_name, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)


class Reservation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reservation_number = models.CharField(max_length=14, unique=True, editable=False, null=True)

    STATUS_CHOICES = [
        ('active', _('New')),
        ('completed', _('Completed')),
        ('cancelled_by_customer', _('Cancelled by Customer')),
        ('cancelled_by_seller', _('Cancelled by Seller')),
    ]

    service = models.ForeignKey(
        BookingService, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name=_("Service")
    )
    provider = models.ForeignKey(
        Provider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reservations',
        verbose_name=_("Provider")
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='my_bookings',
        verbose_name=_("Customer")
    )
    
    start_time = models.DateTimeField(_("Start Time"))
    
    # Делаем время окончания необязательным, так как для брони 'на конкретное время' его может не быть
    end_time = models.DateTimeField(_("End Time"), null=True, blank=True)
    
    customer_comment = models.TextField(_("Customer Comment"), blank=True, max_length=500)
    status = models.CharField(_("Status"), max_length=30, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']

    def generate_reservation_number(self):
        chars = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(chars) for _ in range(10))
        return f"R-{code}"

    def save(self, *args, **kwargs):
        if not self.reservation_number:
            new_number = self.generate_reservation_number()
            while self.__class__.objects.filter(reservation_number=new_number).exists():
                new_number = self.generate_reservation_number()
            self.reservation_number = new_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking #{self.reservation_number or self.id}"


class WorkingHours(models.Model):
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='working_hours',
        verbose_name=_("Owner")
    )
    provider = models.ForeignKey(
        Provider, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='working_hours',
        verbose_name=_("Provider")
    )
    
    day_of_week = models.IntegerField(_("Day of Week"), choices=DAYS_OF_WEEK)
    start_time = models.TimeField(_("Start Time"), default="09:00:00")
    end_time = models.TimeField(_("End Time"), default="18:00:00")
    is_day_off = models.BooleanField(_("Day Off"), default=False)

    class Meta:
        unique_together = ('owner', 'provider', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        prov_name = self.provider.name if self.provider else "General"
        return f"{prov_name} - {self.get_day_of_week_display()}"