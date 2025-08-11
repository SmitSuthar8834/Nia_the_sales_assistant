"""
Django settings for NIA Sales Assistant project.

This file contains all configuration settings for the NIA Sales Assistant application.
Environment variables are used for sensitive data and deployment-specific settings.

For more information on Django settings:
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CORE DJANGO SETTINGS
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# Generate a new secret key for production using:
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-j06!@5-k(z-92a&k2l7vq_f#(6$2&w5urv_s=vtlqq&ckk@u4*",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# Hosts/domain names that this Django site can serve
# In production, set this to your actual domain names
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,testserver").split(
    ","
)

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

# Django applications installed in this project
INSTALLED_APPS = [
    # Django core applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party applications
    "rest_framework",  # Django REST Framework for API endpoints
    "channels",        # Django Channels for WebSocket support
    
    # NIA Sales Assistant applications
    "users",           # User management and authentication
    "ai_service",      # AI-powered sales recommendations
    "voice_service",   # Voice processing and real-time communication
    "meeting_service", # Meeting scheduling and management
    "admin_config",    # Administrative configuration interface
]

# Middleware configuration - order matters!
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",      # Security headers and HTTPS
    "django.contrib.sessions.middleware.SessionMiddleware",  # Session management
    "django.middleware.common.CommonMiddleware",          # Common functionality
    "django.middleware.csrf.CsrfViewMiddleware",         # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # User authentication
    "django.contrib.messages.middleware.MessageMiddleware",     # Message framework
    "django.middleware.clickjacking.XFrameOptionsMiddleware",   # Clickjacking protection
]

# URL configuration module
ROOT_URLCONF = "nia_sales_assistant.urls"

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Custom template directory
        "APP_DIRS": True,  # Look for templates in app directories
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI application for deployment
WSGI_APPLICATION = "nia_sales_assistant.wsgi.application"


# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Default to SQLite for development, PostgreSQL for production
# To use PostgreSQL, set DB_NAME environment variable
if config('DB_NAME', default=''):
    # PostgreSQL configuration for production
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='password'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 60,
            },
        }
    }
else:
    # SQLite configuration for development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ==============================================================================
# AUTHENTICATION AND SECURITY
# ==============================================================================

# Custom user model
AUTH_USER_MODEL = "users.User"

# Password validation configuration
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC FILES CONFIGURATION
# ==============================================================================

# URL prefix for static files
STATIC_URL = "/static/"

# Directories to search for static files during development
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Directory where static files are collected for production
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==============================================================================
# MODEL CONFIGURATION
# ==============================================================================

# Default primary key field type for new models
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# ==============================================================================

REST_FRAMEWORK = {
    # Authentication classes for API endpoints
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Default permissions for API endpoints
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Response rendering classes
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Pagination configuration
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ==============================================================================
# AI SERVICE CONFIGURATION
# ==============================================================================

# Gemini AI API Configuration
GEMINI_API_KEY = config("GEMINI_API_KEY")
GEMINI_API_KEY_BACKUP = config("GEMINI_API_KEY_BACKUP", default="")

# Support for multiple API keys for load balancing
GEMINI_API_KEYS = (
    config("GEMINI_API_KEYS", default="").split(",")
    if config("GEMINI_API_KEYS", default="")
    else [GEMINI_API_KEY]
)

# API quota limits to prevent exceeding Gemini API limits
GEMINI_MINUTE_LIMIT = config("GEMINI_MINUTE_LIMIT", default=15, cast=int)
GEMINI_DAILY_LIMIT = config("GEMINI_DAILY_LIMIT", default=1500, cast=int)
GEMINI_TOKEN_MINUTE_LIMIT = config("GEMINI_TOKEN_MINUTE_LIMIT", default=1000000, cast=int)

# ==============================================================================
# CELERY CONFIGURATION (Background Tasks)
# ==============================================================================

# Redis broker configuration for Celery
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")

# Celery serialization settings
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ==============================================================================
# GOOGLE CLOUD INTEGRATION
# ==============================================================================

# Google Cloud project configuration (optional)
GOOGLE_CLOUD_PROJECT = config("GOOGLE_CLOUD_PROJECT", default="")
GOOGLE_APPLICATION_CREDENTIALS = config("GOOGLE_APPLICATION_CREDENTIALS", default="")

# Google Meet OAuth2 configuration for calendar integration
GOOGLE_MEET_CLIENT_ID = config("GOOGLE_MEET_CLIENT_ID", default="")
GOOGLE_MEET_CLIENT_SECRET = config("GOOGLE_MEET_CLIENT_SECRET", default="")
GOOGLE_MEET_REDIRECT_URI = config(
    "GOOGLE_MEET_REDIRECT_URI", 
    default="http://localhost:8000/meeting/oauth/callback/"
)

# Required OAuth2 scopes for Google Meet integration
GOOGLE_MEET_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/meetings.space.readonly",
]

# ==============================================================================
# MICROSOFT TEAMS INTEGRATION
# ==============================================================================

# Microsoft OAuth2 configuration for Teams/Outlook integration
MICROSOFT_CLIENT_ID = config("MICROSOFT_CLIENT_ID", default="")
MICROSOFT_CLIENT_SECRET = config("MICROSOFT_CLIENT_SECRET", default="")
MICROSOFT_TENANT_ID = config("MICROSOFT_TENANT_ID", default="common")
MICROSOFT_REDIRECT_URI = config(
    "MICROSOFT_REDIRECT_URI",
    default="http://localhost:8000/meeting/oauth/outlook/callback/",
)

# ==============================================================================
# DJANGO CHANNELS CONFIGURATION (WebSocket Support)
# ==============================================================================

# ASGI application for WebSocket support
ASGI_APPLICATION = "nia_sales_assistant.asgi.application"

# Channel layers configuration using Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://localhost:6379/0")],
        },
    },
}
