import os
from pathlib import Path
from decouple import config
import dj_database_url

# ----------------------------------------------------------
# BASE PATH
# ----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------
# SECURITY
# ----------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="dev-secret-key")
DEBUG = config("DEBUG", default="True") == "True"

ALLOWED_HOSTS = ["*"]   # For Render this is fine; you can restrict later.


# ----------------------------------------------------------
# INSTALLED APPS
# ----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",

    # Your app
    "core",
]


# ----------------------------------------------------------
# MIDDLEWARE
# ----------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    # whitenoise for static file serving
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    # locale must be here
    "django.middleware.locale.LocaleMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]


# ----------------------------------------------------------
# URLS & TEMPLATES
# ----------------------------------------------------------
ROOT_URLCONF = "farmlink.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
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

WSGI_APPLICATION = "farmlink.wsgi.application"


# ----------------------------------------------------------
# DATABASE (Auto switch SQLite <-> Render PostgreSQL)
# ----------------------------------------------------------

# Priority 1 → DATABASE_URL (Render)
DATABASES = {
    "default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Priority 2 → Manual Postgres via .env
if config("USE_POSTGRES", default="False") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": config("POSTGRES_DB"),
            "USER": config("POSTGRES_USER"),
            "PASSWORD": config("POSTGRES_PASSWORD"),
            "HOST": config("POSTGRES_HOST", default="localhost"),
            "PORT": config("POSTGRES_PORT", default="5432"),
        }
    }


# ----------------------------------------------------------
# AUTH USER MODEL
# ----------------------------------------------------------
AUTH_USER_MODEL = "core.User"


# ----------------------------------------------------------
# STATIC / MEDIA
# ----------------------------------------------------------
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ----------------------------------------------------------
# CORS / API
# ----------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ]
}


# ----------------------------------------------------------
# MULTILINGUAL SUPPORT
# ----------------------------------------------------------
LANGUAGE_CODE = "en"

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGES = [
    ("en", "English"),
    ("hi", "Hindi"),
    ("kn", "Kannada"),
    ("te", "Telugu"),
    ("ta", "Tamil"),
    ("ml", "Malayalam"),
    ("mr", "Marathi"),
    ("gu", "Gujarati"),
    ("bn", "Bengali"),
    ("pa", "Punjabi"),
    ("or", "Odia"),
    ("as", "Assamese"),
    ("ur", "Urdu"),
    ("ne", "Nepali"),
    ("sd", "Sindhi"),
    ("sa", "Sanskrit"),
]
