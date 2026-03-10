from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Provider(models.Model):
    # Исполнитель (сотрудник или сам мастер), привязанный к владельцу кабинета
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='providers',
        verbose_name=_("Owner")
    )
    # Имя исполнителя или название профессии (например, "Анна" или "Мастер маникюра")
    name = models.CharField(_("Name"), max_length=100)
    # Флаг активности, чтобы можно было скрыть уволившегося сотрудника, не удаляя историю
    is_active = models.BooleanField(_("Active"), default=True)
    avatar = models.ImageField(upload_to='providers/', blank=True, null=True, verbose_name="Provider Avatar")
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class BookingService(models.Model):
    # Сама услуга (например, "Мужская стрижка", "Генеральная уборка")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='booking_services',
        verbose_name=_("Owner")
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    # Базовая цена за услугу
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='booking_services/', blank=True, null=True, verbose_name="Service Image")

    def __str__(self):
        return f"{self.title} ({self.owner.username})"


class Reservation(models.Model):
    # Возможные статусы бронирования для отслеживания отмен
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('cancelled_by_customer', _('Cancelled by Customer')),
        ('cancelled_by_seller', _('Cancelled by Seller')),
    ]

    # Связь с конкретной услугой
    service = models.ForeignKey(
        BookingService, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name=_("Service")
    )
    # Связь с исполнителем (on_delete=models.SET_NULL сохранит чек, если исполнителя удалят)
    # null=True и blank=True позволяют создать бронь без привязки к конкретному человеку
    provider = models.ForeignKey(
        Provider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reservations',
        verbose_name=_("Provider")
    )
    # Клиент, который забронировал слот
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='my_bookings',
        verbose_name=_("Customer")
    )
    
    # Точное время начала и конца брони (будет формироваться из выделенных 15-минутных слотов)
    start_time = models.DateTimeField(_("Start Time"))
    end_time = models.DateTimeField(_("End Time"))
    
    # Текстовое поле для комментария клиента при оформлении
    customer_comment = models.TextField(_("Customer Comment"), blank=True, max_length=500)
    status = models.CharField(_("Status"), max_length=30, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Сортировка по умолчанию: сначала самые новые (будущие) записи
        ordering = ['-start_time']

    def __str__(self):
        return f"Booking #{self.id} - {self.service.title}"
    

class WorkingHours(models.Model):
    # Фиксированный список дней недели для формирования базового расписания
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    # Владелец расписания (продавец)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='working_hours',
        verbose_name=_("Owner")
    )
    # Привязка к конкретному исполнителю. Если пусто — это общее расписание для услуги без мастера.
    provider = models.ForeignKey(
        Provider, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='working_hours',
        verbose_name=_("Provider")
    )
    
    day_of_week = models.IntegerField(_("Day of Week"), choices=DAYS_OF_WEEK)
    
    # Время начала и окончания рабочего дня
    start_time = models.TimeField(_("Start Time"), default="09:00:00")
    end_time = models.TimeField(_("End Time"), default="18:00:00")
    
    # Флаг выходного дня (если True, слоты на этот день генерироваться не будут)
    is_day_off = models.BooleanField(_("Day Off"), default=False)

    class Meta:
        # Предотвращаем создание дублирующихся правил для одного мастера в один и тот же день недели
        unique_together = ('owner', 'provider', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        prov_name = self.provider.name if self.provider else "General"
        return f"{prov_name} - {self.get_day_of_week_display()}"    