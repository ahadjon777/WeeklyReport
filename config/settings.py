import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Lokal tarmoq uchun: SECRET_KEY ni o'zgartirish tavsiya etiladi (env: HISOBOT_SECRET_KEY)
SECRET_KEY = os.environ.get(
    "HISOBOT_SECRET_KEY", "lokal-tarmoq-uchun-ozgartiring-1f7c9a2b5d8e4f60"
)
DEBUG = os.environ.get("HISOBOT_DEBUG", "0") == "1"
# Lokal tarmoqdagi istalgan IP/nom orqali kirish mumkin
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reports",
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
        "DIRS": [],
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

AUTH_PASSWORD_VALIDATORS = []  # lokal tizim: oddiy parollarga ruxsat

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "my_entries"
LOGOUT_REDIRECT_URL = "login"

# Eslatma sozlamalari
# True: brauzer ochiq bo'lsa, sayt ichida ham eslatma oynasi chiqadi
BROWSER_REMINDERS = True
# True: Windows eslatma dasturi bugun hisobot kiritgan xodimni bezovta qilmaydi
REMIND_ONLY_IF_NO_REPORT = False

# Ish kunlari: 0=Dushanba ... 6=Yakshanba
WORK_DAYS = [0, 1, 2, 3, 4]
# Xodim necha kun orqaga qarab hisobot kirita/tahrirlay oladi
BACKFILL_DAYS = 3

# Word hisobot sarlavhasida chiqadigan tashkilot nomi (bo'sh qoldirsangiz chiqmaydi)
ORG_NAME = "Tashkilot nomi"
