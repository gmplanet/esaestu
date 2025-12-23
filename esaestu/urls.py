from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Админка вне i18n_patterns, чтобы URL всегда был /admin/
    path('admin/', admin.site.urls),
    # Стандартный обработчик переключения языков
    path('i18n/', include('django.conf.urls.i18n')),
    path('captcha/', include('captcha.urls')),
    ]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
)