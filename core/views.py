from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Page

def home_view(request):
    return render(request, 'base.html')

def page_detail(request, slug):
    # Поиск по любому слагу остается (это правильно)
    page = get_object_or_404(Page, Q(slug_en=slug) | Q(slug_es=slug))
    return render(request, 'core/page_detail.html', {'page': page})

def search_view(request):
    query = request.GET.get('q', '').strip()
    results_data = []

    if query:
        pages = Page.search(query)
        for page in pages:
            # Если нашли в испанском — переключаем на испанский URL
            if query.lower() in page.title_es.lower() or query.lower() in page.content_es.lower():
                found_lang = 'es'
            else:
                found_lang = 'en'
            
            # Используем универсальные свойства
            results_data.append({
                'title': page.title_es if found_lang == 'es' else page.title_en,
                'url': page.get_url_for_lang(found_lang),
                'lang': found_lang.upper()
            })
    
    return render(request, 'core/search_results.html', {'results': results_data, 'query': query})