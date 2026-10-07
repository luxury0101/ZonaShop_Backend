# ZonaShop Backend

API REST de ZonaShop desarrollada con Django y Django REST Framework. Gestiona el catálogo, la autenticación unificada, los roles, el carrito por cuenta y la documentación OpenAPI.

## Requisitos

- Python 3.12 o superior.
- PostgreSQL.
- Un entorno virtual de Python.

## Instalación en Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y configura una base PostgreSQL de desarrollo. No utilices credenciales de producción en el entorno local.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La API estará disponible en `http://localhost:8000/api/`.

## Variables de entorno

| Variable | Propósito |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave privada utilizada por Django. |
| `DJANGO_DEBUG` | Activa el modo de desarrollo cuando vale `True`. |
| `DJANGO_ALLOWED_HOSTS` | Lista de hosts separados por comas. |
| `DATABASE_URL` | Cadena de conexión PostgreSQL. |
| `CORS_ALLOWED_ORIGINS` | Orígenes autorizados, separados por comas. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF, separados por comas. |
| `DJANGO_SECURE_COOKIES` | Restringe cookies de sesión y CSRF a HTTPS. |
| `DJANGO_SECURE_SSL_REDIRECT` | Redirige las solicitudes HTTP hacia HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS` | Duración de HSTS; debe permanecer en `0` durante desarrollo. |
| `DJANGO_TRUST_PROXY_SSL` | Confía en `X-Forwarded-Proto` del proxy de producción. |
| `DJANGO_COOKIE_SAMESITE` | Política `SameSite` de las cookies. |
| `DJANGO_EMAIL_BACKEND` | Backend de correo; consola en desarrollo y SMTP en producción. |
| `LOGIN_MAX_ATTEMPTS` | Intentos fallidos permitidos antes del bloqueo. |
| `LOGIN_ATTEMPT_WINDOW_SECONDS` | Ventana para contabilizar intentos de acceso. |
| `LOGIN_BLOCK_SECONDS` | Duración del bloqueo por fuerza bruta. |

Los valores seguros se activan automáticamente cuando `DJANGO_DEBUG=False`. Antes de habilitar HSTS, confirma que el dominio y todos los subdominios funcionan permanentemente mediante HTTPS.

## Pruebas

Las pruebas usan una base SQLite en memoria y no modifican PostgreSQL:

```powershell
python manage.py test --settings=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Documentación de la API

Con el servidor en ejecución:

- Esquema OpenAPI: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

## Estructura principal

- `catalogo/`: categorías, productos, existencias y permisos.
- `cuentas/`: registro, sesión, roles, protección CSRF, fuerza bruta y carrito.
- `config/`: configuración, rutas y entornos de Django.

## Documentación técnica

- [Arquitectura y decisiones](docs/arquitectura.md)
- [Matriz de pruebas](docs/matriz-pruebas.md)

## Autenticación y roles

- Registro: `POST /api/auth/registro/`.
- Login unificado: `POST /api/auth/login/`.
- Sesión actual: `GET /api/auth/me/`.
- Cierre de sesión: `POST /api/auth/logout/`.
- Carrito de la cuenta: `GET/PUT /api/auth/carrito/`.

Las contraseñas nuevas se almacenan con Argon2. Los roles disponibles son
`cliente` y `administrador`; el registro público siempre crea clientes. Para
promover una cuenta, cambia el campo `rol` de su `PerfilUsuario` desde Django
Admin. Las operaciones de escritura del catálogo validan este rol en el servidor.
