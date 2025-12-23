from .models import Footer, MenuItem

def menu_processor(request):
    # Получаем первую запись футера из базы
    footer = Footer.objects.first()
    # Получаем только главные пункты меню (без родителей)
    main_menu = MenuItem.objects.filter(parent=None).prefetch_related('children')
    
    return {
        'main_menu': main_menu,
        'footer_content': footer # Эта переменная используется в base.html
    }