from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin # Импортируем специальный класс DraggableMPTTAdmin для создания визуального дерева с кнопками управления
from .models import Page, MenuItem, Maintenance, Footer

admin.site.site_header = "esaestu Administration"
admin.site.index_title = "Site Management"
admin.site.site_title = "esaestu Admin"

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    # Добавили поиск, чтобы легко находить страницы по контенту
    list_display = ('title_en', 'slug_en', 'title_es', 'slug_es')
    search_fields = ('title_en', 'content_en', 'title_es', 'content_es')
    prepopulated_fields = {
        'slug_en': ('title_en',),
        'slug_es': ('title_es',),
    } 
    
    fieldsets = (
        ('English Content', {
            'fields': ('title_en', 'slug_en', 'content_en'),
        }),
        ('Spanish Content', {
            'fields': ('title_es', 'slug_es', 'content_es'),
        }),
    )

@admin.register(MenuItem)
class MenuItemAdmin(DraggableMPTTAdmin):
    # Настраиваем колонки: tree_actions выводит стрелки перемещения, а indented_title отображает наглядные отступы для подпунктов
    list_display = (
        'tree_actions',
        'indented_title',
        'title_en',
        'title_es',
        'linked_page',
        'url',
    )
    # Делаем поле с отступами кликабельным для перехода к редактированию элемента
    list_display_links = ('indented_title',)
    # Оставляем только строку поиска, удаляя старые фильтры и сортировки, так как теперь позиции элементов задаются визуальным перетаскиванием
    search_fields = ('title_en', 'title_es')

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'message_en')

@admin.register(Footer)
class FooterAdmin(admin.ModelAdmin):
    list_display = ('text_en',)