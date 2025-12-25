"""" ESAESTU Django settings for the esaestu project."""
import environ
import os
from pathlib import Path

import ssl

# 1. Настройка путей
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Инициализируем environ
env = environ.Env(
    # Здесь мы сразу задаем типы данных и значения по умолчанию
    DEBUG=(bool, False)
)

# 3. Читаем файл .env, указывая путь к нему через BASE_DIR
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


DEBUG = env('DEBUG')

# 2. Безопасность и Отладка
SECRET_KEY = env.str('SECRET_KEY')


# Обработка хостов с защитой от пустого значения
#ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
# Пропиши это жестко, без env.list
ALLOWED_HOSTS = ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# Добавь это ПРЯМО ТУТ (не в конце файла, а рядом с ALLOWED_HOSTS)
CSRF_TRUSTED_ORIGINS = ['https://esaestu.casa', 'https://www.esaestu.casa']


# Включаем HSTS на 1 год (в секундах)
SECURE_HSTS_SECONDS = 31536000 

# Рекомендуется также добавить эти две настройки:
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Применять ко всем поддоменам
SECURE_HSTS_PRELOAD = True             # Позволяет включить сайт в глобальный список HSTS


# Запрещает встраивать твой сайт в <iframe> на чужих ресурсах (защита от кликджекинга)
X_FRAME_OPTIONS = 'DENY'

# Защита от подмены типов контента
SECURE_CONTENT_TYPE_NOSNIFF = True







# 3. Определение приложений
INSTALLED_APPS = [
    'core',
    'accounts',
    'captcha',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# 4. Middleware (порядок важен для LocaleMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # Должен быть после Session и перед Common
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'esaestu.urls'

# 5. Шаблоны и контекстные процессоры
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
                'core.context_processors.menu_processor', # Твой процессор для меню и футера
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



# 7. Валидация паролей (важно для будущего этапа регистрации)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 8. Интернационализация (i18n)
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
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# Папка, куда соберутся все файлы при деплое (python manage.py collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Настройки для загружаемых файлов (аватарки, документы и т.д.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




# Пользовательская модель пользователя

AUTH_USER_MODEL = 'accounts.CustomUser'


# Эта настройка заставляет Django проверять флаг is_active при логине
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailVerifiedBackend', # Наш новый строгий бэкенд
    'django.contrib.auth.backends.ModelBackend', # Оставляем стандартный для админки
]

# 10. Перенаправления после логина/логаута
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Email settings

if DEBUG:
    # Локально: выводим письма в консоль (без ошибок SSL) 📝
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # На сервере: отправляем через настоящий Gmail 📧
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = env.str('EMAIL_HOST_USER', default='webmaster@localhost')



# Настройки безопасности для продакшена
if not DEBUG:
    # Перенаправлять все HTTP запросы на HTTPS
    SECURE_SSL_REDIRECT = True

    # Защита куки сессии (передавать только по HTTPS)
    SESSION_COOKIE_SECURE = True

    # Защита куки CSRF (передавать только по HTTPS)
    CSRF_COOKIE_SECURE = True

    # Защита от подмены протокола за прокси-сервером (Nginx)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    CSRF_TRUSTED_ORIGINS = ['https://esaestu.casa', 'https://www.esaestu.casa']

# Настройка логирования только для сервера
if not DEBUG:
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
                # Используем переменную окружения для пути, чтобы не «хардкодить» его
                'filename': os.getenv('DJANGO_LOG_PATH', '/var/www/esaestu/logs/django_error.log'),
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



