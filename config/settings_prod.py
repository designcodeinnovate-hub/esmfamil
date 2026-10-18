import os
import dj_database_url
from .settings import *

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()] or ["*"]

_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if _csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf.split(",") if u.strip()]

if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, ssl_require=False)
    }

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

_redis = os.environ.get("REDIS_URL", "")
if _redis:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [_redis]},
        }
    }


# ============================================================
# CSRF & Security (FIXED)
# ============================================================
_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if _csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf.split(",") if u.strip()]
else:
    # Fallback: allow current Runflare domain
    CSRF_TRUSTED_ORIGINS = [
        "https://esmfamil-c78-esmfamil-db.runflare.cloud",
        "https://esmfamil.com",
        "https://www.esmfamil.com",
    ]

# Make sure ALLOWED_HOSTS includes runflare domain
_runflare = "esmfamil-c78-esmfamil-db.runflare.cloud"
if _runflare not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_runflare)
if "esmfamil.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("esmfamil.com")
if "www.esmfamil.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("www.esmfamil.com")

# SSL proxy header (critical for CSRF behind proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ===== Security (auto-added) =====
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 0
