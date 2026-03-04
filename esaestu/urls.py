from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Админка вне i18n_patterns
    path('admin/', admin.site.urls),
    # Стандартный обработчик переключения языков
    path('i18n/', include('django.conf.urls.i18n')),
    
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),

    # 1. Сначала подключаем allauth. 
    # Он заберет на себя /profile_app/login/, /profile_app/signup/ и т.д.
    path('account/', include('allauth.urls')),



    # 2. Затем твое приложение. 
    # Если там есть пути, которых нет в allauth (например, 'profile/'), они будут работать.
    path('account/', include('profile_app.urls')),

    
 
    

)