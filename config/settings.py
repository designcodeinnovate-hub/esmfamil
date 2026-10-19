import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [
    "esmfamil-c78-esmfamil-db.runflare.cloud",
    "esmfamil.com",
    "www.esmfamil.com",
    "127.0.0.1",
    "localhost",
]  # Allow all hosts (safe for now)

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "accounts",
    "game",
    "social",
    "alliance",
    "channels",

    "common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- CORS (dev only) ---
CORS_ALLOW_ALL_ORIGINS = True

# --- Email (dev: چاپ لینک در کنسول ترمینال runserver) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "spdmax2010@gmail.com"
EMAIL_HOST_PASSWORD = "gidbmiflvwzqizih"
DEFAULT_FROM_EMAIL = "noreply@esmfamil.local"
BACKEND_URL = "http://127.0.0.1:8000"

# --- Login redirect for @login_required ---
LOGIN_URL = "/accounts/login/"
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
LOGIN_REDIRECT_URL = "/game/"

# ============================================================
# PRODUCTION SAFETY BLOCK (always applied)
# ============================================================

# --- CSRF Trusted Origins (critical for Runflare/proxy) ---
CSRF_TRUSTED_ORIGINS = [
    "https://esmfamil-c78-esmfamil-db.runflare.cloud",
    "https://esmfamil.com",
    "https://www.esmfamil.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
# Also add any from env var
_csrf_env = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if _csrf_env:
    for origin in _csrf_env.split(","):
        origin = origin.strip()
        if origin and origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# --- Proxy SSL header (for HTTPS behind proxy) ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Database from env (PostgreSQL on Runflare) ---
if os.environ.get("DATABASE_URL"):
    try:
        import dj_database_url
        DATABASES = {
            "default": dj_database_url.config(
                conn_max_age=600,
                ssl_require=False,
                conn_health_checks=True,
            )
        }
    except ImportError:
        pass

# --- WhiteNoise for static files ---
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Login URLs (fix for @login_required) ---
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/game/"

# --- Cookie settings (safe for HTTP and HTTPS) ---
# If you later get real HTTPS, set these to True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False  # JS needs to read CSRF token

# --- X-Frame-Options ---
X_FRAME_OPTIONS = "SAMEORIGIN"

# ============================================================
# FINAL PRODUCTION FIX (always applied)
# ============================================================

# 1. Trust Runflare domain for CSRF (critical!)
CSRF_TRUSTED_ORIGINS = [
    "https://esmfamil-c78-esmfamil-db.runflare.cloud",
    "https://esmfamil.com",
    "https://www.esmfamil.com",
]

# 2. Tell Django it is behind an HTTPS proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 3. Ensure cookies work correctly in this environment
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

