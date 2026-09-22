from django.urls import path

from .views import crear_checkout, listar_pedidos, webhook_wompi

urlpatterns = [
    path("", listar_pedidos, name="listar-pedidos"),
    path("checkout/", crear_checkout, name="crear-checkout"),
    path("wompi/webhook/", webhook_wompi, name="webhook-wompi"),
]
