from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "clave-local-para-el-trabajo-practico"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "biblioteca",
]

MIDDLEWARE = []
ROOT_URLCONF = "biblioteca_project.urls"
TEMPLATES = []
WSGI_APPLICATION = "biblioteca_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
