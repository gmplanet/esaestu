from django.shortcuts import render, get_object_or_404
from django.db.models import Q
# Импортируем функцию для безопасного получения активной модели пользователя
from django.contrib.auth import get_user_model
from .models import Page

# Инициализируем модель пользователя для дальнейших запросов к базе данных
User = get_user_model()

def home_view(request):
    # Выполняем запрос к базе данных для поиска пользователей
    # Параметр groups__name='Seller' фильтрует только тех, кто состоит в группе продавцов
    # Метод distinct() исключает дублирование записей, если пользователь состоит в нескольких группах
    creators = User.objects.filter(groups__name='Seller').distinct()
    
    # Возвращаем рендер шаблона base.html, передавая в него словарь с переменной creators
    return render(request, 'base.html', {'creators': creators})

def page_detail(request, slug):
    # Поиск страницы по слагу на английском или испанском языке
    page = get_object_or_404(Page, Q(slug_en=slug) | Q(slug_es=slug))
    # Рендеринг шаблона детальной страницы с передачей найденного объекта
    return render(request, 'core/page_detail.html', {'page': page})

def search_view(request):
    # Получаем поисковой запрос из параметров GET и удаляем лишние пробелы по краям
    query = request.GET.get('q', '').strip()
    # Создаем пустой список для хранения отформатированных результатов поиска
    results_data = []

    # Проверяем, не пустой ли запрос
    if query:
        # Вызываем метод поиска из модели Page
        pages = Page.search(query)
        # Проходим циклом по всем найденным страницам
        for page in pages:
            # Проверяем наличие искомого текста в испанском заголовке или контенте
            if query.lower() in page.title_es.lower() or query.lower() in page.content_es.lower():
                # Устанавливаем язык найденного совпадения как испанский
                found_lang = 'es'
            else:
                # В противном случае устанавливаем язык как английский
                found_lang = 'en'
            
            # Добавляем словарь с данными о странице в общий список результатов
            results_data.append({
                # Выбираем правильный заголовок в зависимости от определенного языка
                'title': page.title_es if found_lang == 'es' else page.title_en,
                # Получаем корректный URL для выбранного языка
                'url': page.get_url_for_lang(found_lang),
                # Переводим код языка в верхний регистр для отображения (ES или EN)
                'lang': found_lang.upper()
            })
    
    # Возвращаем рендер шаблона поиска с результатами и исходным запросом
    return render(request, 'core/search_results.html', {'results': results_data, 'query': query})


def home_view(request):
    # Добавляем параметр show_in_catalog=True в фильтр. 
    # База данных вернет только тех продавцов, которые явно разрешили показ в ленте.
    creators = User.objects.filter(groups__name='Seller', show_in_catalog=True).distinct()
    
    return render(request, 'base.html', {'creators': creators})