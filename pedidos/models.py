from django.conf import settings
from django.db import models

from catalogo.models import Producto
from clientes.models import Direccion


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE_PAGO = "PENDIENTE_PAGO", "Pendiente de pago"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        PAGO_RECHAZADO = "PAGO_RECHAZADO", "Pago rechazado"
        CANCELADO = "CANCELADO", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    direccion = models.ForeignKey(
        Direccion,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    referencia = models.CharField(max_length=64, unique=True)
    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.PENDIENTE_PAGO,
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    inventario_liberado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-creado_en"]


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
    )
    nombre_producto = models.CharField(max_length=150)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


class Pago(models.Model):
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name="pago",
    )
    proveedor = models.CharField(max_length=30, default="WOMPI")
    transaccion_id = models.CharField(max_length=100, blank=True, default="")
    estado = models.CharField(max_length=30, default="PENDING")
    actualizado_en = models.DateTimeField(auto_now=True)
