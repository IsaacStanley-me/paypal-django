"""
Django settings for paypal_project.
Configured for Railway deployment with WhiteNoise static-file support.
"""

from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


# Load .env if python-dotenv is available
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


# Security settings
# Set DJANGO_SECRET_KEY in Railway Variables to a long random value.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-only-change-me",
)

DEBUG = False


# Allowed hosts
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "paypal-django-production.up.railway.app",
    "evercrestpay.com",
    "www.evercrestpay.com",
]


# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://paypal-django-production.up.railway.app",
    "https://evercrestpay.com",
    "https://www.evercrestpay.com",
]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",

    # Local apps
    "accounts",
    "home",
    "rewards",
    "wallet",
    "transactions",
]


# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.InactivityLogoutMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "paypal_project.urls"


# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "paypal_project.wsgi.application"


# Database
# On Railway, DATABASE_URL points to Postgres, so data survives redeploys.
# Locally (no DATABASE_URL), it falls back to SQLite.
if os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            env="DATABASE_URL",
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
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


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True


# Supported languages
LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
    ("ar", "Arabic"),
    ("ru", "Russian"),
    ("ko", "Korean"),
    ("nl", "Dutch"),
    ("tr", "Turkish"),
    ("hi", "Hindi"),
    ("sw", "Swahili"),
]


# Translation files
LOCALE_PATHS = [
    BASE_DIR / "locale",
]


# Static files
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# WhiteNoise static-file storage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}


# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Custom user model
AUTH_USER_MODEL = "accounts.User"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# Language cookie
LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = "Lax"


# Session / inactivity settings
SESSION_COOKIE_AGE = 300
SESSION_SAVE_EVERY_REQUEST = True


# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = 10  # seconds; stops a blocked SMTP connection from hanging the app
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)


# Logging: print errors to the console so they appear in Railway logs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
