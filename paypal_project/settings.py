"""
 Django settings for paypal_project.
 Restored to a minimal working configuration for local development.
 """

from pathlib import Path
import os
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if python-dotenv is available
if load_dotenv is not None:
    load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-recovered-temp-key-change-me",
)

# For local development. Set to False in production.
DEBUG = True

# Hosts allowed to serve this site
ALLOWED_HOSTS: list[str] = [
    "localhost",
    "127.0.0.1",
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

MIDDLEWARE = [
     "django.middleware.security.SecurityMiddleware",
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
TIME_ZONE = "UTC"
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

# Where to find compiled translations
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF basic settings (optional minimal)
REST_FRAMEWORK = {
     "DEFAULT_AUTHENTICATION_CLASSES": [
         "rest_framework.authentication.SessionAuthentication",
         "rest_framework.authentication.BasicAuthentication",
     ],
     "DEFAULT_PERMISSION_CLASSES": [
         "rest_framework.permissions.IsAuthenticated",
     ],
 }

# in paypal_project/settings.py
LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 year
LANGUAGE_COOKIE_SAMESITE = "Lax"

# Session / inactivity settings (5 minutes)
SESSION_COOKIE_AGE = 300  # 5 minutes
SESSION_SAVE_EVERY_REQUEST = True  # refresh expiry on each request while active

# Email (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'icicibankweb@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'hrbj ypdo jkhz dboo')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ICICI Bank <icicibankweb@gmail.com>')