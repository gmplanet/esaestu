from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from .models import Page
from shop_app.models import Product
from booking_app.models import BookingService


User = get_user_model()

def home_view(request):
    query = request.GET.get('q', '').strip()
    active_filter = request.GET.get('filter', 'all')
    
    # Оптимизируем запрос: заранее грузим только АКТИВНЫЕ товары и услуги
    users_qs = User.objects.prefetch_related(
        Prefetch('products', queryset=Product.objects.filter(is_active=True)),
        'booking_services'
    )
    pages_qs = Page.objects.none()
    

    if active_filter == 'shop':
        users_qs = users_qs.filter(Q(groups__name='Seller') | Q(is_superuser=True)).distinct()
    elif active_filter == 'booking':
        users_qs = users_qs.filter(Q(groups__name='Booking') | Q(is_superuser=True)).distinct()
    elif active_filter == 'pages':
        users_qs = User.objects.none()
        pages_qs = Page.objects.all()
    else:
        users_qs = users_qs.filter(
            Q(groups__name__in=['Seller', 'Booking', 'Photographer', 'Blogger']) | 
            Q(is_superuser=True)
        ).distinct()
        pages_qs = Page.objects.all()

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(products__title__icontains=query) |
            Q(products__description__icontains=query) |
            Q(booking_services__title__icontains=query) |
            Q(booking_services__description__icontains=query)
        ).distinct()
        
        if active_filter in ['all', 'pages']:
            pages_qs = Page.objects.filter(
                Q(title_en__icontains=query) | 
                Q(content_en__icontains=query) |
                Q(title_es__icontains=query) | 
                Q(content_es__icontains=query)
            ).distinct()

    combined_list = list(users_qs.order_by('-id')) + list(pages_qs.order_by('-id'))
    
    paginator = Paginator(combined_list, 7)  # 7 элементов на страницу
    page_number = request.GET.get('page', 1)

    # Проверяем, является ли запрос AJAX-запросом от скрипта
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Метод page() строго проверяет существование страницы
            feed_items = paginator.page(page_number)
            return render(request, 'includes/user_card_partial_loop.html', {'feed_items': feed_items})
        except (EmptyPage, PageNotAnInteger):
            # Если страницы нет, отдаем пустой ответ, чтобы скрипт остановился
            return HttpResponse('')

    # Обычная загрузка страницы
    feed_items = paginator.get_page(page_number)
    
    return render(request, 'home.html', {
        'feed_items': feed_items,
        'active_filter': active_filter,
        'query': query
    })

def page_detail(request, slug):
    page = get_object_or_404(Page, Q(slug_en=slug) | Q(slug_es=slug))
    return render(request, 'core/page_detail.html', {'page': page})