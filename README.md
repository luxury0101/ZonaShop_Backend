# ZonaShop Backend

API REST de ZonaShop desarrollada con Django y Django REST Framework. Gestiona el catálogo, la autenticación administrativa, los permisos y la documentación OpenAPI.

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
- `cuentas/`: sesión administrativa y protección CSRF.
- `config/`: configuración, rutas y entornos de Django.
