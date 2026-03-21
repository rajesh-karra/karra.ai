import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

_allowed_hosts_raw = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
_default_allowed_hosts = ["localhost", "127.0.0.1", "0.0.0.0", ".app.github.dev"]
_env_allowed_hosts = [
    host.strip()
    for host in _allowed_hosts_raw.split(",")
    if host.strip()
]
ALLOWED_HOSTS = list(dict.fromkeys([*_default_allowed_hosts, *_env_allowed_hosts]))


def _normalize_origin(origin_or_host: str) -> list[str]:
    value = origin_or_host.strip()
    if not value:
        return []

    if value.startswith(("http://", "https://")):
        return [value]

    if value in {"localhost", "127.0.0.1", "[::1]"}:
        return [f"http://{value}", f"https://{value}"]

    origins = [f"https://{value}"]
    if DEBUG:
        origins.append(f"http://{value}")
    return origins


_env_csrf_origins = [
    entry.strip()
    for entry in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if entry.strip()
]

_default_csrf_inputs = [*ALLOWED_HOSTS, *_env_csrf_origins]
_default_csrf_inputs.append("https://*.app.github.dev")
if DEBUG:
    _default_csrf_inputs.extend([
        "localhost",
        "localhost:8000",
        "127.0.0.1",
        "127.0.0.1:8000",
    ])

CSRF_TRUSTED_ORIGINS = sorted(
    {
        origin
        for item in _default_csrf_inputs
        for origin in _normalize_origin(item)
    }
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "portfolio",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/dbname?sslmode=require",
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "False").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("DJANGO_SESSION_COOKIE_SECURE", "False").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("DJANGO_CSRF_COOKIE_SECURE", "False").lower() == "true"
SESSION_COOKIE_SAMESITE = os.getenv("DJANGO_SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("DJANGO_CSRF_COOKIE_SAMESITE", "Lax")

# Caching configuration for performance optimization
# Use local memory cache with reasonable timeouts
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "karra-cache",
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
        }
    }
}

