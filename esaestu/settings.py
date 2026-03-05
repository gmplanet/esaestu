#███████╗███████╗ █████╗ ███████╗███████╗████████╗██╗   ██╗
#██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║   ██║
#█████╗  ███████╗███████║█████╗  ███████╗   ██║   ██║   ██║
#██╔══╝  ╚════██║██╔══██║██╔══╝  ╚════██║   ██║   ██║   ██║
#███████╗███████║██║  ██║███████╗███████║   ██║   ╚██████╔╝
#╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ 
                                                          
import environ
import os
from pathlib import Path

# 1. Настройка путей
BASE_DIR = Path(__file__).resolve().parent.parent


# 2. Инициализируем environ
env = environ.Env(
    DEBUG=(bool, False)
)

# 3. Читаем файл .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# Безопасность и Отладка
DEBUG = env('DEBUG')
SECRET_KEY = env.str('SECRET_KEY') 

# Настройка хостов
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# 3. Определение приложений
INSTALLED_APPS = [
    'core',
    'profile_app',
    
    # Обязательно: admin_interface и его зависимость colorfield должны стоять строго ДО django.contrib.admin
    'admin_interface',
    'colorfield',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Ваша новая Google капча
    'django_recaptcha',
    
    # Приложения для Allauth:
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_rename_app',
    
    # Подключение новых загруженных библиотек
    'django_ckeditor_5', # Интеграция визуального редактора текста
    'imagekit',          # Инструмент для автоматической обработки и обрезки изображений
    'mptt',              # Утилита для работы с древовидными структурами (например, для вложенных категорий)
    
    # Обязательно: пакет для автоматического удаления связанных файлов должен быть самым последним в списке
    'django_cleanup.apps.CleanupConfig',
]

SITE_ID = 1

# 4. Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MaintenanceModeMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'esaestu.urls'

# 5. Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.menu_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'esaestu.wsgi.application'

# 6. База данных
DATABASES = {
    'default': env.db(
        'DATABASE_URL', 
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

# 7. Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 8. Интернационализация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# 9. Статические и Медиа файлы
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Модель пользователя
AUTH_USER_MODEL = 'profile_app.CustomUser'

# Email settings
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = env.str('EMAIL_HOST_USER', default='webmaster@localhost')

# === ФИНАЛЬНЫЙ БЛОК БЕЗОПАСНОСТИ ===

if not DEBUG:
    # Настройки для сервера (PRODUCTION)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS настройки (для рейтинга A+)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    CSRF_TRUSTED_ORIGINS = ['https://esaestu.casa', 'https://www.esaestu.casa']
    
    # Логирование только для сервера
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': env.str('DJANGO_LOG_PATH', default='/var/www/esaestu/logs/django_error.log'),
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }
else:
    # Настройки для твоего компьютера (DEVELOPMENT)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    # Локально разрешаем HTTP для работы с CSRF
    CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']




AUTHENTICATION_BACKENDS = [
    # 1. Ваш кастомный бэкенд (оставляем первым)
    'profile_app.backends.EmailVerifiedBackend',
    
    # 2. Стандартный бэкенд Django
    'django.contrib.auth.backends.ModelBackend',
    
    # 3. Бэкенд для входа через соцсети (Google)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Куда перенаправлять пользователя после входа
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True


# Настройки Allauth — Современный синтаксис 2025

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Это одна настройка заменяет собой все ACCOUNT_EMAIL_REQUIRED, 
# ACCOUNT_USERNAME_REQUIRED и прочие. 
# Звездочка * означает "обязательно".
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# Это оставляем, так как это связь с вашей моделью CustomUser
ACCOUNT_USER_MODEL_USERNAME_FIELD = None



# Остальные настройки оставляем без изменений
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PROTOCOL': 'https',
    }
}

RECAPTCHA_PUBLIC_KEY = env.str('RECAPTCHA_PUBLIC_KEY', default='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
RECAPTCHA_PRIVATE_KEY = env.str('RECAPTCHA_PRIVATE_KEY', default='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')


ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'


# Пользователь не будет считаться залогиненным, пока не подтвердит почту
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# Не логинить автоматически сразу после регистрации
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/profile_app/login/'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/profile/'


ACCOUNT_FORMS = {
    'signup': 'profile_app.forms.CustomSignupForm',
}



ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/600s'
}







# === НАСТРОЙКИ DJANGO-ADMIN-INTERFACE ===
# Разрешаем загрузку iframe-контента с того же домена (необходимо для работы модальных окон)
X_FRAME_OPTIONS = "SAMEORIGIN"

# Подавляем системное предупреждение W019, так как мы осознанно изменили политику X_FRAME_OPTIONS
SILENCED_SYSTEM_CHECKS = ["security.W019"]








# === НАСТРОЙКИ DJANGO-CKEDITOR-5 ===
# Указываем директорию внутри вашего MEDIA_ROOT, куда будут сохраняться картинки из редактора
CKEDITOR_5_UPLOADS_FOLDER = "ckeditor5_uploads/"

# Глобальная конфигурация панелей инструментов
CKEDITOR_5_CONFIGS = {
    # 'default' - базовая панель для небольших полей
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload'],
    },
    # 'extends' - расширенная панель с исходным кодом, таблицами и выравниванием изображений
    'extends': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    '|', 'bulletedList', 'numberedList', '|', 'blockQuote', 'imageUpload',
                    'insertTable', 'mediaEmbed', 'removeFormat', 'sourceEditing'],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side'],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter']
        },
    }
}