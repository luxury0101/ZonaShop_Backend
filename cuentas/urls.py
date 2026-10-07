from django.urls import path

from .views import (
    carrito_usuario,
    cerrar_sesion,
    consultar_sesion,
    iniciar_sesion,
    obtener_csrf,
    pedidos_usuario,
    pedidos_administracion,
    actualizar_estado_pedido,
    perfil_usuario,
    registrar_usuario,
)


app_name = "cuentas"

urlpatterns = [
    path("csrf/", obtener_csrf, name="obtener-csrf"),
    path("registro/", registrar_usuario, name="registro"),
    path("login/", iniciar_sesion, name="iniciar-sesion"),
    path("logout/", cerrar_sesion, name="cerrar-sesion"),
    path("me/", consultar_sesion, name="consultar-sesion"),
    path("perfil/", perfil_usuario, name="perfil"),
    path("carrito/", carrito_usuario, name="carrito"),
    path("pedidos/", pedidos_usuario, name="pedidos"),
    path("admin/pedidos/", pedidos_administracion, name="pedidos-administracion"),
    path(
        "admin/pedidos/<uuid:numero>/",
        actualizar_estado_pedido,
        name="actualizar-estado-pedido",
    ),
]
