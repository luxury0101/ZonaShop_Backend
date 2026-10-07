# Matriz de pruebas de ZonaShop

## Ejecución automatizada

Backend:

```powershell
python manage.py test --settings=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate --file schema.yml
```

Frontend:

```powershell
npm test
npm run build
npm audit
```

GitHub Actions ejecuta estos controles en cada `push` y solicitud de cambio.

## Casos de aceptación

| ID | Caso | Evidencia actual | Estado |
| --- | --- | --- | --- |
| PR-01 | Crear una categoría válida | Prueba de creación mediante la API. | Automatizado |
| PR-02 | Crear un producto con categoría existente | `test_administrador_puede_crear_y_editar_productos`. | Automatizado |
| PR-03 | Rechazar precio o existencias inválidas | `test_api_rechaza_datos_invalidos_de_producto`. | Automatizado |
| PR-04 | Editar el precio de un producto | Pruebas de edición administrativa y CSRF. | Automatizado |
| PR-05 | Impedir eliminar categorías con productos | `test_no_se_elimina_categoria_con_productos`. | Automatizado |
| PR-06 | Filtrar el catálogo | `test_catalogo_es_publico_y_filtra_por_categoria`. | Automatizado |
| PR-07 | Modificar cantidades del carrito | Pruebas DOM de cantidades, existencias y total. | Automatizado |
| PR-08 | Restaurar y revalidar el carrito | Pruebas de precio, stock, eliminación y error de conexión. | Automatizado |
| PR-09 | Rechazar modificaciones sin permisos | Pruebas de usuario anónimo y usuario no administrador. | Automatizado |
| PR-10 | Rechazar escritura sin CSRF | `test_modificacion_con_sesion_requiere_csrf`. | Automatizado |
| PR-11 | Tratar HTML como texto | Prueba de API y uso de `textContent` en la interfaz. | Automatizado y revisión de código |
| PR-12 | Informar fallos de conexión | Prueba del cliente HTTP y mensajes visibles del catálogo y carrito. | Automatizado y revisión visual |
| PR-13 | Acceder desde otro dispositivo | Requiere dirección pública y HTTPS. | Pendiente de despliegue |
| PR-14 | Conservar datos después de redespliegue | Requiere PostgreSQL y entorno publicado. | Pendiente de despliegue |

## Control previo al despliegue

No se inicia el despliegue mientras falle alguno de estos controles:

- Pruebas del backend.
- Pruebas y build del frontend.
- Validación de OpenAPI.
- Detección de migraciones sin crear.
- Auditoría de dependencias.
- `manage.py check --deploy` con variables de producción simuladas.

Después del despliegue se ejecutarán PR-13 y PR-14, además de una repetición manual de los recorridos principales.
