from pathlib import Path
from datetime import timedelta
from environs import env

env.read_env()

DEBUG = env.bool("DEBUG")
SECRET_KEY = env.str("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", [])

BASE_DIR = Path(__file__).resolve().parent.parent


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'drf_spectacular',
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "user",
    "matching",
    "chats",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

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

WSGI_APPLICATION = "core.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER", "postgres"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST", "localhost"),
        "PORT": env.str("DB_PORT", "5432"),
    }
}


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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

AUTH_USER_MODEL = "user.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Email (Gmail SMTP app password)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SPECTACULAR_SETTINGS = {
    "TITLE": "AIBuddy API",
    "DESCRIPTION": """
## Overview
API-only backend for auth, matching/invites, and chats (AI + direct).

## Authentication
- Uses JWT (SimpleJWT).
- Login: `POST /api/auth/login/`
- Send `Authorization: Bearer <access_token>` for protected endpoints.
- Logout: `POST /api/auth/logout/` with refresh token.

## Registration (4-step flow)
1. `POST /api/auth/register/email/` -> send verification code to email
2. `POST /api/auth/register/verify/` -> verify code, returns `session_token`
3. `POST /api/auth/register/password/` -> set password
4. `POST /api/auth/register/complete/` -> set profile and interests

## Interests
- List options: `GET /api/auth/interests/`

## Matching + Invites
- `GET /api/matching/candidates/` -> similar-interest users without existing direct chat
- `POST /api/matching/invites/` -> send invite
- `GET /api/matching/invites/incoming/`
- `GET /api/matching/invites/outgoing/`
- `POST /api/matching/invites/{invite_id}/accept/` -> creates direct chat if needed
- `POST /api/matching/invites/{invite_id}/reject/`

## Chats
- Select/create chat: `POST /api/chats/select/`
  - AI chat: `{ "mode": "ai" }`
  - Direct chat: `{ "mode": "person", "peer_id": <id> }`
- List chats: `GET /api/chats/`
- Chat detail/messages: `GET /api/chats/{chat_id}/`
- Send message: `POST /api/chats/{chat_id}/messages/`

## AI Commands
Supported in AI chat, and command-only in direct chat:
- `#topic` or `#topic <custom topic>`
- `#task`
- `#hint`
- `#answer <your answer>`
- `#evaluate`
""",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
