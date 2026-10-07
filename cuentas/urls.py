from django.urls import path

from .views import (
    carrito_usuario,
    cerrar_sesion,
    consultar_sesion,
    iniciar_sesion,
    obtener_csrf,
    pedidos_usuario,
    registrar_usuario,
)


app_name = "cuentas"

urlpatterns = [
    path("csrf/", obtener_csrf, name="obtener-csrf"),
    path("registro/", registrar_usuario, name="registro"),
    path("login/", iniciar_sesion, name="iniciar-sesion"),
    path("logout/", cerrar_sesion, name="cerrar-sesion"),
    path("me/", consultar_sesion, name="consultar-sesion"),
    path("carrito/", carrito_usuario, name="carrito"),
    path("pedidos/", pedidos_usuario, name="pedidos"),
]
