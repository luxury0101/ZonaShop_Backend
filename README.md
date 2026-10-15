# ZonaShop Backend

API REST de ZonaShop desarrollada con Django y Django REST Framework. Gestiona
el catálogo, usuarios, roles, carrito, pedidos, inventario y el pago simulado.

## Guía rápida para trabajar en Windows

Esta guía asume que se utilizará PowerShell y que el frontend se instalará en
otra carpeta al lado de este repositorio.

### 1. Instalar los programas necesarios

Antes de comenzar, instala:

- [Git](https://git-scm.com/download/win).
- [Python 3.12 o superior](https://www.python.org/downloads/). Durante la
  instalación activa **Add Python to PATH**.
- [PostgreSQL](https://www.postgresql.org/download/windows/). Conserva la
  contraseña que asignes al usuario `postgres`.
- Node.js se necesita para el frontend, no para este repositorio.

Comprueba las instalaciones desde PowerShell:

```powershell
git --version
python --version
psql --version
```

Si `psql` no se reconoce, abre **SQL Shell (psql)** desde el menú Inicio o crea
la base de datos con pgAdmin.

### 2. Clonar los dos repositorios

```powershell
New-Item -ItemType Directory -Path ZonaShop -Force
Set-Location ZonaShop
git clone https://github.com/luxury0101/ZonaShop_Backend.git
git clone https://github.com/luxury0101/ZonaShop_Front.git
```

La estructura debe quedar así:

```text
ZonaShop/
├── ZonaShop_Backend/
└── ZonaShop_Front/
```

### 3. Crear la base de datos de desarrollo

Ejecuta estos comandos y escribe la contraseña del usuario `postgres` cuando se
solicite:

```powershell
psql -U postgres -c "CREATE USER zonashop_dev WITH PASSWORD 'zonashop_dev';"
psql -U postgres -c "CREATE DATABASE zonashop OWNER zonashop_dev;"
```

La contraseña anterior es únicamente para desarrollo local. Nunca debe usarse
en producción. Si el usuario o la base ya existen, no necesitas recrearlos.

### 4. Crear y activar el entorno virtual

```powershell
Set-Location ZonaShop_Backend
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Cuando el entorno esté activo, PowerShell mostrará `(venv)` al inicio de la
línea. Cada vez que abras otra terminal para el backend debes ejecutar:

```powershell
Set-Location ZonaShop_Backend
.\venv\Scripts\Activate.ps1
```

### 5. Crear el archivo `.env`

Desde la carpeta `ZonaShop_Backend`, copia y ejecuta todo este bloque:

```powershell
$zonashopSecret = python -c "import secrets; print(secrets.token_urlsafe(50))"
@"
DJANGO_SECRET_KEY=$zonashopSecret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://zonashop_dev:zonashop_dev@localhost:5432/zonashop
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
DJANGO_SECURE_COOKIES=False
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False
DJANGO_TRUST_PROXY_SSL=False
DJANGO_COOKIE_SAMESITE=Lax
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
LOGIN_MAX_ATTEMPTS=5
LOGIN_ATTEMPT_WINDOW_SECONDS=900
LOGIN_BLOCK_SECONDS=900
"@ | Set-Content -Encoding utf8 .env
```

El archivo `.env` contiene información privada y está ignorado por Git. No se
debe subir ni compartir por chat.

### 6. Preparar Django

Con `(venv)` activo, ejecuta:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py check
```

`createsuperuser` solicitará correo, nombre de usuario y contraseña. Esa cuenta
puede iniciar sesión desde el mismo formulario del frontend y tendrá acceso al
panel administrativo.

### 7. Iniciar el backend

```powershell
python manage.py runserver
```

Déjalo ejecutándose. Las direcciones principales son:

- API: `http://localhost:8000/api/`
- Swagger: `http://localhost:8000/api/docs/`
- Django Admin: `http://localhost:8000/admin/`

Después abre una segunda terminal y sigue el README del frontend.

## Comandos de uso diario

```powershell
Set-Location ZonaShop_Backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

Para ejecutar las comprobaciones antes de subir cambios:

```powershell
python manage.py test --settings=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run
```

Las pruebas utilizan SQLite y no modifican la base PostgreSQL de desarrollo.

## Variables de entorno

| Variable | Propósito |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave privada utilizada por Django. |
| `DJANGO_DEBUG` | Activa el modo de desarrollo cuando vale `True`. |
| `DJANGO_ALLOWED_HOSTS` | Hosts autorizados, separados por comas. |
| `DATABASE_URL` | Cadena de conexión PostgreSQL. |
| `CORS_ALLOWED_ORIGINS` | Orígenes autorizados, separados por comas. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF. |
| `DJANGO_SECURE_COOKIES` | Restringe las cookies a HTTPS. |
| `DJANGO_SECURE_SSL_REDIRECT` | Redirige HTTP hacia HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS` | Duración de HSTS; debe ser `0` localmente. |
| `DJANGO_TRUST_PROXY_SSL` | Confía en el proxy HTTPS de producción. |
| `DJANGO_COOKIE_SAMESITE` | Política `SameSite` de las cookies. |
| `DJANGO_EMAIL_BACKEND` | Sistema utilizado para enviar correos. |
| `LOGIN_MAX_ATTEMPTS` | Intentos fallidos permitidos. |
| `LOGIN_ATTEMPT_WINDOW_SECONDS` | Ventana para contabilizar intentos. |
| `LOGIN_BLOCK_SECONDS` | Duración del bloqueo por fuerza bruta. |

Los valores seguros se activan automáticamente cuando `DJANGO_DEBUG=False`.

## Estructura principal

- `catalogo/`: categorías, productos, imágenes, existencias y permisos.
- `cuentas/`: registro, sesión, roles, perfil, carrito, pedidos y compra.
- `config/`: configuración, rutas y entornos de Django.
- `docs/`: arquitectura y matriz de pruebas.
- `media/`: imágenes subidas localmente; no forman parte del código.

## Autenticación y pedidos

- Registro: `POST /api/auth/registro/`.
- Login: `POST /api/auth/login/`.
- Sesión actual: `GET /api/auth/me/`.
- Cierre de sesión: `POST /api/auth/logout/`.
- Perfil: `GET/PATCH /api/auth/perfil/`.
- Carrito: `GET/PUT /api/auth/carrito/`.
- Pedidos y compra: `GET/POST /api/auth/pedidos/`.
- Administración de pedidos: `GET /api/auth/admin/pedidos/`.

Las contraseñas se almacenan con Argon2. El servidor recalcula los precios,
valida el stock y crea el pedido dentro de una transacción. La simulación de
pago nunca recibe ni almacena el número de tarjeta o el CVV.

## Solución de problemas

- **`python` no se reconoce:** reinstala Python activando **Add Python to PATH**.
- **No se pueden ejecutar scripts:** vuelve a ejecutar
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- **Error de conexión a PostgreSQL:** confirma que el servicio PostgreSQL esté
  iniciado y que `DATABASE_URL` coincida con el usuario, contraseña y base.
- **Puerto 8000 ocupado:** usa `python manage.py runserver 8001` y cambia también
  `VITE_API_BASE_URL` en el frontend.
- **El navegador rechaza la sesión:** utiliza `localhost` en ambos proyectos;
  evita mezclar `localhost` con `127.0.0.1`.

## Información que GitHub no incluye

Al clonar se obtiene el código, pero no se descargan:

- El archivo `.env`.
- La base de datos local y sus usuarios.
- Las imágenes existentes dentro de `media/`.

Cada desarrollador debe crear su propia base, ejecutar las migraciones y crear
su cuenta administrativa.

## Documentación técnica

- [Arquitectura y decisiones](docs/arquitectura.md)
- [Matriz de pruebas](docs/matriz-pruebas.md)
