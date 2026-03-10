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
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext as _



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
                # Если следующий слот начинается ровно там, где заканчивается предыдущий - продлеваем время окончания
                current_end = slot + timedelta(minutes=15)
            else:
                # Если цепочка прервалась, сохраняем накопленный блок как отдельную запись
                reservations_to_create.append(Reservation(
                    service=service,
                    provider=provider,
                    customer=request.user,
                    start_time=current_start,
                    end_time=current_end,
                    customer_comment=safe_comment
                ))
                # Начинаем собирать новый блок
                current_start = slot
                current_end = slot + timedelta(minutes=15)

        # Добавляем последний собранный блок
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
            # Двойная проверка, чтобы два человека одновременно не заняли одно место
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

        # ФОРМИРОВАНИЕ И ОТПРАВКА EMAIL УВЕДОМЛЕНИЙ
        buyer = request.user
        seller = service.owner
        
        provider_info = f" ({provider.name})" if provider else ""
        booking_details = "\n".join([f"• {r.start_time.strftime('%Y-%m-%d %H:%M')} - {r.end_time.strftime('%H:%M')}" for r in reservations_to_create])
        
        # Письмо покупателю
        buyer_subject = _("Booking Confirmed: %(service)s") % {'service': service.title}
        buyer_message = _(
            "Hello %(buyer)s,\n\n"
            "Your booking for %(service)s%(provider)s is confirmed!\n\n"
            "Time slots:\n%(details)s\n\n"
            "Total slots booked: %(count)s\n"
        ) % {
            'buyer': buyer.username,
            'service': service.title,
            'provider': provider_info,
            'details': booking_details,
            'count': len(slots)
        }

        # Письмо продавцу (исполнителю)
        seller_subject = _("New Booking: %(service)s") % {'service': service.title}
        seller_message = _(
            "Hello %(seller)s,\n\n"
            "You have a new booking from %(buyer)s for %(service)s%(provider)s.\n\n"
            "Time slots:\n%(details)s\n\n"
            "Customer comment: %(comment)s\n"
        ) % {
            'seller': seller.username,
            'buyer': buyer.username,
            'service': service.title,
            'provider': provider_info,
            'details': booking_details,
            'comment': safe_comment if safe_comment else _("No comment provided")
        }

        try:
            send_mail(buyer_subject, buyer_message, settings.DEFAULT_FROM_EMAIL, [buyer.email], fail_silently=True)
            send_mail(seller_subject, seller_message, settings.DEFAULT_FROM_EMAIL, [seller.email], fail_silently=True)
        except Exception:
            pass # Игнорируем ошибки отправки почты, чтобы не прерывать процесс для пользователя

        return JsonResponse({'status': 'success', 'message': _('Booking confirmed successfully!')})

    except Exception as e:
        
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    


@login_required
def cabinet_my_bookings(request):
    # Получаем все бронирования, где текущий пользователь является клиентом
    # order_by('-start_time') сортирует список от новых к старым
    bookings = Reservation.objects.filter(customer=request.user).order_by('-start_time')
    return render(request, 'booking_app/cabinet_my_bookings.html', {'bookings': bookings})

@login_required
def cabinet_incoming_bookings(request):
    # Проверяем наличие прав продавца услуг
    if not request.user.groups.filter(name='Booking').exists():
        raise PermissionDenied("You do not have permission to access this module.")
    
    # Получаем все бронирования, где текущий пользователь является владельцем услуги
    bookings = Reservation.objects.filter(service__owner=request.user).order_by('-start_time')
    return render(request, 'booking_app/cabinet_incoming_bookings.html', {'bookings': bookings})

@require_POST
@login_required
def cancel_booking(request, booking_id):
    # Находим конкретную запись в базе данных
    reservation = get_object_or_404(Reservation, id=booking_id)
    
    # Проверяем, имеет ли текущий пользователь право отменять эту запись
    is_customer = request.user == reservation.customer
    is_seller = request.user == reservation.service.owner
    
    if not (is_customer or is_seller):
        raise PermissionDenied("You cannot cancel this booking.")
        
    # Если бронь уже отменена, ничего не делаем и возвращаем обратно
    if reservation.status != 'active':
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    # Меняем статус в зависимости от того, кто нажал кнопку отмены
    if is_customer:
        reservation.status = 'cancelled_by_customer'
        canceler = "Customer"
    else:
        reservation.status = 'cancelled_by_seller'
        canceler = "Seller"
        
    # Сохраняем новый статус в базу данных
    reservation.save()
    
    # ФОРМИРОВАНИЕ ПИСЕМ ОБ ОТМЕНЕ
    subject = _("Booking Cancelled: %(service)s") % {'service': reservation.service.title}
    message = _(
        "The booking for %(service)s on %(date)s at %(time)s has been cancelled by the %(canceler)s.\n\n"
        "Booking ID: %(id)s"
    ) % {
        'service': reservation.service.title,
        'date': reservation.start_time.strftime('%Y-%m-%d'),
        'time': reservation.start_time.strftime('%H:%M'),
        'canceler': canceler,
        'id': reservation.id
    }
    
    # Отправляем одно и то же письмо сразу обоим участникам (клиенту и продавцу)
    try:
        send_mail(
            subject, 
            message, 
            settings.DEFAULT_FROM_EMAIL, 
            [reservation.customer.email, reservation.service.owner.email], 
            fail_silently=True
        )
    except Exception:
        pass
        
    # Возвращаем пользователя на ту страницу, с которой он нажал кнопку отмены
    return redirect(request.META.get('HTTP_REFERER', '/'))    

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