# booking_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Маршрут для главной страницы модуля бронирования в личном кабинете
    path('cabinet/booking/', views.cabinet_booking_list, name='cabinet_booking_list'),
    # Маршрут для страницы создания новой услуги
    path('cabinet/booking/service/add/', views.cabinet_service_add, name='cabinet_service_add'),
    # Маршруты для редактирования и удаления услуги
    path('cabinet/booking/service/<int:service_id>/edit/', views.booking_edit_service, name='booking_edit_service'),
    path('cabinet/booking/service/<int:service_id>/delete/', views.booking_delete_service, name='booking_delete_service'),
    
    # Маршрут для страницы добавления нового исполнителя
    path('cabinet/booking/provider/add/', views.cabinet_provider_add, name='cabinet_provider_add'),
    # Маршруты для редактирования и удаления исполнителя
    path('cabinet/booking/provider/<int:provider_id>/edit/', views.booking_edit_provider, name='booking_edit_provider'),
    path('cabinet/booking/provider/<int:provider_id>/delete/', views.booking_delete_provider, name='booking_delete_provider'),
    
    # Маршрут для общего расписания (без привязки к конкретному человеку)
    path('cabinet/booking/schedule/', views.cabinet_schedule_manage, name='cabinet_schedule_manage_general'),
    # Маршрут для расписания конкретного мастера
    path('cabinet/booking/schedule/<int:provider_id>/', views.cabinet_schedule_manage, name='cabinet_schedule_manage_provider'),

    path('b/<slug:slug>/', views.public_booking_view, name='public_booking'),
    # API для получения свободных слотов
    path('api/slots/', views.api_get_available_slots, name='api_get_available_slots'),
    # API для подтверждения и сохранения бронирования
    path('api/confirm/', views.api_confirm_booking, name='api_confirm_booking'),
    # Маршрут для клиента: просмотр своих записей
    path('cabinet/my-bookings/', views.cabinet_my_bookings, name='cabinet_my_bookings'),
    # Маршрут для продавца: просмотр входящих резерваций
    path('cabinet/incoming-bookings/', views.cabinet_incoming_bookings, name='cabinet_incoming_bookings'),
    # Маршрут-обработчик для отмены бронирования
    path('cabinet/booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
]