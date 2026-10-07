from .settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Las pruebas usan el cliente HTTP interno de Django. Estas opciones se
# validan por separado con ``manage.py check --deploy`` y no deben convertir
# cada petición de prueba en una redirección HTTPS.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

