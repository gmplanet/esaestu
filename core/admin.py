from django.contrib import admin
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
class MenuItemAdmin(admin.ModelAdmin):
    # Добавили колонку родителя и фильтр
    list_display = ('title_en', 'title_es', 'parent', 'order', 'url')
    list_editable = ('order',)
    list_filter = ('parent',) # Удобно фильтровать подпункты
    search_fields = ('title_en', 'title_es')

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'message_en')

@admin.register(Footer)
class FooterAdmin(admin.ModelAdmin):
    list_display = ('text_en',)