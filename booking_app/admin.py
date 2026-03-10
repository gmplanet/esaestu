from django.contrib import admin
from .models import BookingService, Provider, Reservation, WorkingHours

# Создаем специальный класс-встройку (Inline).
# TabularInline выводит связанные данные в виде удобной горизонтальной таблицы.
class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    # Указываем поля, которые можно будет просматривать и редактировать прямо в этой таблице
    fields = ('day_of_week', 'start_time', 'end_time', 'is_day_off')
    # extra = 0 означает, что Django не будет выводить дополнительные пустые строки для новых записей
    extra = 0
    # Жестко сортируем дни по порядку (от понедельника к воскресенью)
    ordering = ('day_of_week',)

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'owner__username')
    # Встраиваем нашу таблицу часов работы прямо внутрь страницы редактирования Исполнителя
    inlines = [WorkingHoursInline]

@admin.register(BookingService)
class BookingServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'owner__username')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'provider', 'customer', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'start_time')
    search_fields = ('service__title', 'customer__username', 'provider__name')

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('owner', 'provider', 'day_of_week', 'start_time', 'end_time', 'is_day_off')
    list_filter = ('day_of_week', 'is_day_off', 'owner')
    ordering = ('owner', 'provider', 'day_of_week')
    # Добавляем поиск по юзернейму владельца, его email и имени исполнителя
    search_fields = ('owner__username', 'owner__email', 'provider__name')