"""
Django settings for health_consultation project.

Barangay Guimbala Online Health Consultation System
Silay City, Negros Occidental, Philippines
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-barangay-guimbala-health-consultation-secret-key-2024'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Local apps
    'accounts.apps.AccountsConfig',
    'appointments.apps.AppointmentsConfig',
    'chat.apps.ChatConfig',
    'consultations.apps.ConsultationsConfig',
    'notifications.apps.NotificationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'health_consultation.urls'

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
                'notifications.context_processors.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'health_consultation.wsgi.application'
ASGI_APPLICATION = 'health_consultation.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.tjcbxhrppvxhutcpuoey:%2B6Wm%23%2A%23i%26H%2B7XXC@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres",
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required. Configure your Supabase Postgres URL.")

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Login settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'home'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Email settings (for production, configure these)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Messages settings
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Jitsi / JaaS settings
# For JaaS, set:
# JITSI_DOMAIN=8x8.vc
# JITSI_APP_ID=vpaas-magic-cookie-...
# Optional temporary token for testing:
# JITSI_JWT=<jwt>
JITSI_DOMAIN = os.getenv('JITSI_DOMAIN', 'meet.jit.si')
JITSI_APP_ID = os.getenv('JITSI_APP_ID', '')
JITSI_JWT = os.getenv('JITSI_JWT', '')
