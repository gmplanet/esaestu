# booking_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
# Импортируем все необходимые модели базы данных для работы контроллеров
from .models import BookingService, Provider, WorkingHours, Reservation
from .forms import BookingServiceForm, ProviderForm
from django.forms import modelformset_factory
from .forms import WorkingHoursForm
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from django.db.models import Q
from core.tasks import send_async_email



# Контроллер для отображения главной страницы управления бронированием в личном кабинете
@login_required
def cabinet_booking_list(request):
    # Проверяем, состоит ли пользователь в группе 'Booking'
    # Администратор должен создать эту группу в админке и добавлять туда пользователей для выдачи прав
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")
        
    # Получаем все услуги, которые принадлежат текущему авторизованному пользователю
    services = BookingService.objects.filter(owner=request.user)
    # Получаем всех исполнителей, которые принадлежат текущему пользователю
    providers = Provider.objects.filter(owner=request.user)
    
    # Передаем данные в шаблон для отображения списков
    return render(request, 'booking_app/cabinet_booking_list.html', {
        'services': services,
        'providers': providers
    })

# Контроллер для добавления новой услуги через личный кабинет
@login_required
def cabinet_service_add(request):
    # Повторная проверка прав доступа для безопасности маршрута
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")
        
    # Если метод POST, значит пользователь нажал кнопку отправки заполненной формы
    if request.method == 'POST':
        form = BookingServiceForm(request.POST)
        # Проверяем правильность введенных данных (типы полей, обязательность)
        if form.is_valid():
            # Создаем объект услуги, но пока откладываем сохранение в базу (commit=False)
            service = form.save(commit=False)
            # Присваиваем текущего пользователя как владельца услуги
            service.owner = request.user
            # Теперь окончательно сохраняем запись в базу данных
            service.save()
            # Перенаправляем обратно к общему списку услуг и исполнителей
            return redirect('cabinet_booking_list')
    # Если метод GET (обычный переход по ссылке), просто показываем пустую форму
    else:
        form = BookingServiceForm()
        
    return render(request, 'booking_app/cabinet_service_add.html', {
        'form': form
    })

# Контроллер для добавления нового исполнителя (мастера)
@login_required
def cabinet_provider_add(request):
    # Ограничение доступа только для провайдеров услуг
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")
        
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            # Жестко привязываем создаваемого исполнителя к текущему пользователю-владельцу
            provider.owner = request.user
            provider.save()
            return redirect('cabinet_booking_list')
    else:
        form = ProviderForm()
        
    return render(request, 'booking_app/cabinet_provider_add.html', {
        'form': form
    })

@login_required
def cabinet_schedule_manage(request, provider_id=None):
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")

    provider = None
    if provider_id:
        # Если передан ID, ищем конкретного исполнителя
        provider = get_object_or_404(Provider, id=provider_id, owner=request.user)

    # Автоматически создаем пустые записи для всех 7 дней недели, если их еще нет в базе.
    # Это избавит пользователя от необходимости вручную нажимать "создать понедельник", "создать вторник" и т.д.
    for day in range(7):
        WorkingHours.objects.get_or_create(
            owner=request.user,
            provider=provider,
            day_of_week=day,
            defaults={'start_time': '09:00', 'end_time': '18:00', 'is_day_off': False}
        )

    # Создаем "набор форм" (FormSet) для редактирования массива данных без лишнего кода
    WorkingHoursFormSet = modelformset_factory(WorkingHours, form=WorkingHoursForm, extra=0)
    
    # Получаем график только для текущего пользователя и выбранного мастера (или общего расписания)
    queryset = WorkingHours.objects.filter(owner=request.user, provider=provider).order_by('day_of_week')

    if request.method == 'POST':
        formset = WorkingHoursFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            return redirect('cabinet_booking_list')
    else:
        formset = WorkingHoursFormSet(queryset=queryset)

    return render(request, 'booking_app/cabinet_schedule_manage.html', {
        'formset': formset,
        'provider': provider
    })

def public_booking_view(request, slug):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Находим продавца по слагу. Если его нет или он не в группе Booking, вернется 404
    seller = get_object_or_404(User, slug=slug, groups__name='Booking')
    
    # Получаем только активные услуги и активных исполнителей
    services = BookingService.objects.filter(owner=seller, is_active=True)
    providers = Provider.objects.filter(owner=seller, is_active=True)

    return render(request, 'booking_app/public_booking.html', {
        'seller': seller,
        'services': services,
        'providers': providers,
    })



def api_get_available_slots(request):
    # Получаем данные из AJAX-запроса браузера
    service_id = request.GET.get('service_id')
    provider_id = request.GET.get('provider_id')
    date_str = request.GET.get('date')

    if not service_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        # Преобразуем строку даты (YYYY-MM-DD) в объект Python
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Определяем день недели (0 - Понедельник, 6 - Воскресенье)
    weekday = target_date.weekday()

    service = BookingService.objects.filter(id=service_id).first()
    if not service:
        return JsonResponse({'error': 'Service not found'}, status=404)

    # Если передан ID исполнителя, ищем его, иначе None (общее расписание)
    provider = None
    if provider_id:
        provider = Provider.objects.filter(id=provider_id).first()

    # Ищем настроенные рабочие часы для этого дня недели
    working_hours = WorkingHours.objects.filter(
        owner=service.owner,
        provider=provider,
        day_of_week=weekday
    ).first()

    # Если расписание не настроено или стоит галочка "Выходной" - отдаем пустой список
    if not working_hours or working_hours.is_day_off:
        return JsonResponse({'slots': []})

    # Создаем точные объекты времени начала и конца рабочего дня (с учетом часового пояса сервера)
    start_dt = timezone.make_aware(datetime.combine(target_date, working_hours.start_time))
    end_dt = timezone.make_aware(datetime.combine(target_date, working_hours.end_time))

    # Достаем из базы ВСЕ активные бронирования на этот день для этого мастера
    reservations = Reservation.objects.filter(
        service=service,
        provider=provider,
        start_time__lt=end_dt,
        end_time__gt=start_dt,
        status='active'
    )

    slots = []
    current_dt = start_dt

    # Цикл: шагаем по 15 минут от начала до конца рабочего дня
    while current_dt + timedelta(minutes=15) <= end_dt:
        slot_end = current_dt + timedelta(minutes=15)
        is_booked = False
        
        # Проверяем, не пересекается ли наш 15-минутный слот с какой-либо существующей бронью
        for res in reservations:
            if max(current_dt, res.start_time) < min(slot_end, res.end_time):
                is_booked = True
                break
                
        # Теперь мы добавляем ВСЕ слоты, но передаем флаг is_booked
        slots.append({
            'time': current_dt.strftime('%H:%M'),
            'datetime': current_dt.isoformat(),
            'is_booked': is_booked
        })
            
        current_dt += timedelta(minutes=15)

    return JsonResponse({'slots': slots})

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@require_POST
@login_required
def api_confirm_booking(request):
    try:
        # Получаем данные от JavaScript
        data = json.loads(request.body)
        service_id = data.get('service_id')
        provider_id = data.get('provider_id')
        slots = data.get('slots', [])
        comment = data.get('comment', '')

        if not slots or not service_id:
            return JsonResponse({'status': 'error', 'message': _('Invalid data')}, status=400)

        # БЕЗОПАСНОСТЬ: Очищаем комментарий от HTML/JS тегов и жестко обрезаем до 250 символов
        safe_comment = strip_tags(comment)[:250]

        service = BookingService.objects.filter(id=service_id).first()
        if not service:
            return JsonResponse({'status': 'error', 'message': _('Service not found')}, status=404)

        provider = Provider.objects.filter(id=provider_id).first() if provider_id else None

        # Преобразуем текстовые даты в объекты datetime и сортируем их
        parsed_slots = sorted([parse_datetime(s) for s in slots])

        reservations_to_create = []
        current_start = parsed_slots[0]
        # Задаем конец первого слота (+ 15 минут)
        current_end = current_start + timedelta(minutes=15)

        # Алгоритм склеивания подряд идущих 15-минутных слотов в одну длинную запись
        for slot in parsed_slots[1:]:
            if slot == current_end:
                current_end = slot + timedelta(minutes=15)
            else:
                reservations_to_create.append(Reservation(
                    service=service,
                    provider=provider,
                    customer=request.user,
                    start_time=current_start,
                    end_time=current_end,
                    customer_comment=safe_comment
                ))
                current_start = slot
                current_end = slot + timedelta(minutes=15)

        reservations_to_create.append(Reservation(
            service=service,
            provider=provider,
            customer=request.user,
            start_time=current_start,
            end_time=current_end,
            customer_comment=safe_comment
        ))

        # Сохраняем все сформированные бронирования в базу данных
        for res in reservations_to_create:
            conflict = Reservation.objects.filter(
                service=service,
                provider=provider,
                start_time__lt=res.end_time,
                end_time__gt=res.start_time,
                status='active'
            ).exists()
            
            if conflict:
                return JsonResponse({'status': 'error', 'message': _('Some slots were already booked. Please refresh the page.')}, status=400)
            
            res.save()

        # --- ФОРМИРОВАНИЕ И ОТПРАВКА EMAIL УВЕДОМЛЕНИЙ ---
        buyer = request.user
        seller = service.owner
        
        # Формируем имя мастера, если он выбран
        provider_info = f" ({provider.name})" if provider else ""
        # Собираем все забронированные слоты в красивый список
        booking_details = "\n".join([f"• {r.start_time.strftime('%Y-%m-%d')} | {r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}" for r in reservations_to_create])
        
        # Подготовка подробного письма покупателю (клиенту)
        buyer_subject = _("Booking Confirmed: %(service)s") % {'service': service.title}
        buyer_message = _(
            "Hello %(buyer)s!\n\n"
            "Your booking for %(service)s%(provider)s is confirmed.\n\n"
            "Reservation Details:\n%(details)s\n\n"
            "Total slots booked: %(count)s\n\n"
            "Thank you for your reservation!"
        ) % {
            'buyer': buyer.username,
            'service': service.title,
            'provider': provider_info,
            'details': booking_details,
            'count': len(slots)
        }

        # Подготовка подробного письма продавцу (владельцу сервиса)
        seller_subject = _("New Booking: %(service)s") % {'service': service.title}
        seller_message = _(
            "Hello %(seller)s!\n\n"
            "You have a new reservation from %(buyer)s for %(service)s%(provider)s.\n\n"
            "Customer Information:\n"
            "Email: %(email)s\n\n"
            "Reservation Details:\n%(details)s\n\n"
            "Customer comment: %(comment)s\n\n"
            "Please check your personal cabinet to manage this booking."
        ) % {
            'seller': seller.username,
            'buyer': buyer.username,
            'email': buyer.email, # Добавлена почта клиента для связи
            'service': service.title,
            'provider': provider_info,
            'details': booking_details,
            'comment': safe_comment if safe_comment else _("No comment provided")
        }

        # Отправляем задачи в очередь Redis (строго 3 аргумента)
        try:
            send_async_email(buyer_subject, buyer_message, [buyer.email])
            send_async_email(seller_subject, seller_message, [seller.email])
        except Exception as e:
            # Выводим ошибку в лог сервера, чтобы она не пропадала бесследно
            print(f"Booking confirmation email error: {e}") 

        return JsonResponse({'status': 'success', 'message': _('Booking confirmed successfully!')})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    


@login_required
def cabinet_my_bookings(request):
    # Начальный запрос: бронирования текущего пользователя как клиента
    bookings = Reservation.objects.filter(customer=request.user)
    
    # Подсчет для вкладок
    counts = {
        'new': bookings.filter(status='active').count(),
        'completed': bookings.filter(status='completed').count(),
        'cancelled': bookings.filter(status__in=['cancelled_by_customer', 'cancelled_by_seller']).count(),
    }
    
    # Фильтрация по вкладкам
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new':
        bookings = bookings.filter(status='active')
    elif current_tab == 'completed':
        bookings = bookings.filter(status='completed')
    elif current_tab == 'cancelled':
        bookings = bookings.filter(status__in=['cancelled_by_customer', 'cancelled_by_seller'])
        
    # Поиск по номеру бронирования или названию услуги/имени продавца
    query = request.GET.get('q', '')
    if query:
        bookings = bookings.filter(
            Q(reservation_number__icontains=query) |
            Q(service__title__icontains=query) |
            Q(service__owner__username__icontains=query)
        ).distinct()
        
    # Сортировка
    sort_by = request.GET.get('sort', '-start_time')
    bookings = bookings.order_by(sort_by)
        
    return render(request, 'booking_app/cabinet_my_bookings.html', {
        'bookings': bookings,
        'counts': counts,
        'current_tab': current_tab,
        'query': query,
        'sort_by': sort_by,
    })

@login_required
def cabinet_incoming_bookings(request):
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")
        
    # Бронирования услуг, принадлежащих текущему пользователю
    bookings = Reservation.objects.filter(service__owner=request.user)
    
    counts = {
        'new': bookings.filter(status='active').count(),
        'completed': bookings.filter(status='completed').count(),
        'cancelled': bookings.filter(status__in=['cancelled_by_customer', 'cancelled_by_seller']).count(),
    }
    
    current_tab = request.GET.get('tab', 'new')
    if current_tab == 'new':
        bookings = bookings.filter(status='active')
    elif current_tab == 'completed':
        bookings = bookings.filter(status='completed')
    elif current_tab == 'cancelled':
        bookings = bookings.filter(status__in=['cancelled_by_customer', 'cancelled_by_seller'])
        
    query = request.GET.get('q', '')
    if query:
        bookings = bookings.filter(
            Q(reservation_number__icontains=query) |
            Q(customer__username__icontains=query) |
            Q(customer__email__icontains=query)
        ).distinct()
        
    sort_by = request.GET.get('sort', '-start_time')
    bookings = bookings.order_by(sort_by)
        
    return render(request, 'booking_app/cabinet_incoming_bookings.html', {
        'bookings': bookings,
        'counts': counts,
        'current_tab': current_tab,
        'query': query,
        'sort_by': sort_by,
    })

@require_POST
@login_required
def cancel_booking(request, booking_uuid):
    reservation = get_object_or_404(Reservation, uuid=booking_uuid)
    
    is_customer = request.user == reservation.customer
    is_seller = request.user == reservation.service.owner
    
    if not (is_customer or is_seller):
        raise PermissionDenied("You cannot cancel this booking.")
        
    if reservation.status == 'active':
        if is_customer:
            reservation.status = 'cancelled_by_customer'
            canceler_name = request.user.username
            canceler_type = _("Customer")
        else:
            reservation.status = 'cancelled_by_seller'
            canceler_name = request.user.username
            canceler_type = _("Seller")
            
        reservation.save()
        
        # --- ФОРМИРОВАНИЕ ПИСЬМА ОБ ОТМЕНЕ ---
        subject = _("Booking Cancelled: #%(number)s") % {'number': reservation.reservation_number}
        
        # Улучшенное форматирование письма об отмене
        message = _(
            "Hello!\n\n"
            "The booking #%(number)s for %(service)s has been cancelled by the %(canceler_type)s (%(canceler_name)s).\n\n"
            "Cancelled Booking Details:\n"
            "• Service: %(service)s\n"
            "• Date: %(date)s\n"
            "• Time: %(time)s - %(end_time)s\n"
            "• Final Status: %(status)s"
        ) % {
            'number': reservation.reservation_number,
            'service': reservation.service.title,
            'date': reservation.start_time.strftime('%Y-%m-%d'),
            'time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'canceler_type': canceler_type,
            'canceler_name': canceler_name,
            'status': reservation.get_status_display()
        }

        # Отправляем задачи в очередь и ловим возможные сбои
        try:
            send_async_email(
                subject, 
                message, 
                [reservation.customer.email, reservation.service.owner.email]
            )
        except Exception as e:
            print(f"Cancel booking email error: {e}")
            
    return redirect('booking_detail', booking_uuid=reservation.uuid)

# Контроллер для редактирования услуги
@login_required
def booking_edit_service(request, service_id):
    service = get_object_or_404(BookingService, id=service_id)
    
    if service.owner != request.user:
        raise PermissionDenied("You do not have permission to edit this service.")
        
    if request.method == 'POST':
        form = BookingServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            return redirect('cabinet_booking_list')
    else:
        form = BookingServiceForm(instance=service)
        
    return render(request, 'booking_app/edit_service.html', {'form': form, 'service': service})

# Контроллер для удаления услуги
@require_POST
@login_required
def booking_delete_service(request, service_id):
    service = get_object_or_404(BookingService, id=service_id)
    
    if service.owner != request.user:
        raise PermissionDenied("You do not have permission to delete this service.")
        
    service.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

# Контроллер для редактирования исполнителя
@login_required
def booking_edit_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)
    
    if provider.owner != request.user:
        raise PermissionDenied("You do not have permission to edit this provider.")
        
    if request.method == 'POST':
        form = ProviderForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            return redirect('cabinet_booking_list')
    else:
        form = ProviderForm(instance=provider)
        
    return render(request, 'booking_app/edit_provider.html', {'form': form, 'provider': provider})

# Контроллер для удаления исполнителя
@require_POST
@login_required
def booking_delete_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)
    
    if provider.owner != request.user:
        raise PermissionDenied("You do not have permission to delete this provider.")
        
    provider.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def booking_detail(request, booking_uuid):
    booking = get_object_or_404(Reservation, uuid=booking_uuid)
    
    # Доступ только участникам
    if request.user != booking.customer and request.user != booking.service.owner:
        raise PermissionDenied()
        
    return render(request, 'booking_app/cabinet_booking_detail.html', {'booking': booking})