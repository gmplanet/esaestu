from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Page
from django.core.paginator import Paginator

# Инициализируем модель пользователя
User = get_user_model()

def home_view(request):
    # Фильтруем продавцов, которые разрешили показ в каталоге
    # Используем order_by, так как пагинация требует стабильной сортировки
    user_list = User.objects.filter(groups__name='Seller', show_in_catalog=True).distinct().order_by('-id')
    
    # Настраиваем пагинацию: по 10 карточек на одну порцию
    paginator = Paginator(user_list, 10)
    page_number = request.GET.get('page')
    creators = paginator.get_page(page_number)

    # Проверяем, является ли запрос AJAX-запросом от нашего JavaScript
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Если это подгрузка, возвращаем только цикл карточек без базового шаблона
        return render(request, 'includes/user_card_partial_loop.html', {'creators': creators})

    # Обычная загрузка страницы (первый заход пользователя)
    # Используем home.html вместо base.html для правильной структуры блоков
    return render(request, 'home.html', {'creators': creators})

def page_detail(request, slug):
    page = get_object_or_404(Page, Q(slug_en=slug) | Q(slug_es=slug))
    return render(request, 'core/page_detail.html', {'page': page})

def search_view(request):
    query = request.GET.get('q', '')
    results_data = []
    
    if query:
        pages = Page.objects.filter(
            Q(title_en__icontains=query) | Q(content_en__icontains=query) |
            Q(title_es__icontains=query) | Q(content_es__icontains=query)
        )
        
        for page in pages:
            if query.lower() in page.title_es.lower() or query.lower() in page.content_es.lower():
                found_lang = 'es'
            else:
                found_lang = 'en'
            
            results_data.append({
                'title': page.title_es if found_lang == 'es' else page.title_en,
                'url': page.get_url_for_lang(found_lang),
                'lang': found_lang.upper()
            })
    
    return render(request, 'core/search_results.html', {'results': results_data, 'query': query})