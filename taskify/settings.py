# taskify/settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️ En producción, mueve la SECRET_KEY a variables de entorno
SECRET_KEY = 'django-insecure-6g^(^%@g&e6o3ey2w=0d&b+ju&dg)awfs0gfpnp8^+-1+reez$'
DEBUG = True

# Para desarrollo local
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "10.0.2.2"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'taskify_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'taskify.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Ruta global a templates para la web clásica
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'taskify_app.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'taskify.wsgi.application'

# Base de datos (sqlite para dev)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validadores de password
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# I18N
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# Static & Media (útil para servir assets en dev)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # crea carpeta /static si la usas
# Para producción con collectstatic:
# STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
# 👉 Por defecto, API PÚBLICA. Luego exiges login por vista/acción.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",  # útil con login de Django (CSRF aplica)
        # "rest_framework_simplejwt.authentication.JWTAuthentication",  # ⬅️ si usas JWT, descomenta e instala simplejwt
        # "rest_framework.authentication.BasicAuthentication",  # opcional
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # ⬅️ clave: por defecto no exige autenticación
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}





