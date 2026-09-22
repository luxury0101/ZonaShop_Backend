from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DireccionViewSet,
    cerrar_sesion_cliente,
    iniciar_sesion_cliente,
    mi_cuenta,
    registrar_cliente,
)

router = DefaultRouter()
router.register("direcciones", DireccionViewSet, basename="direccion")

urlpatterns = [
    path("registro/", registrar_cliente, name="registro-cliente"),
    path("login/", iniciar_sesion_cliente, name="login-cliente"),
    path("logout/", cerrar_sesion_cliente, name="logout-cliente"),
    path("me/", mi_cuenta, name="mi-cuenta"),
    path("", include(router.urls)),
]
