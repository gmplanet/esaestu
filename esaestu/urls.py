from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

# Импортируем инструменты для чтения настроек и генерации ссылок на медиафайлы
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Админка вне i18n_patterns
    path('door13/', admin.site.urls),
    # Стандартный обработчик переключения языков
    path('i18n/', include('django.conf.urls.i18n')),

    path("ckeditor5/", include('django_ckeditor_5.urls')), # Подключаем URL-ы для CKEditor 5
    path('', include('shop_app.urls')),
]
# Включаем i18n_patterns для остальных URL-ов, чтобы они поддерживали мультиязычность
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('account/', include('allauth.urls')),
    path('account/', include('profile_app.urls')),
    path('shop/', include('shop_app.urls')),
        
)



# Включаем раздачу медиафайлов (например, загруженных картинок из редактора) только для локального режима разработки (DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    