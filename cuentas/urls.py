from django.urls import path

from .views import (
    cerrar_sesion,
    consultar_sesion,
    iniciar_sesion,
    obtener_csrf,
)


app_name = "cuentas"


urlpatterns = [
    path(
        "csrf/",
        obtener_csrf,
        name="obtener-csrf",
    ),
    path(
        "login/",
        iniciar_sesion,
        name="iniciar-sesion",
    ),
    path(
        "logout/",
        cerrar_sesion,
        name="cerrar-sesion",
    ),
    path(
        "me/",
        consultar_sesion,
        name="consultar-sesion",
    ),
]