import uuid

from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    class Rol(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        ADMINISTRADOR = "administrador", "Administrador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_zonashop",
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )
    telefono = models.CharField(max_length=20, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    ciudad = models.CharField(max_length=100, blank=True, default="")
    departamento = models.CharField(max_length=100, blank=True, default="")
    codigo_postal = models.CharField(max_length=20, blank=True, default="")
    instrucciones_envio = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"


class IntentoInicioSesion(models.Model):
    """Contador persistente sin guardar correo ni IP en texto plano."""

    clave = models.CharField(max_length=64, unique=True)
    intentos = models.PositiveSmallIntegerField(default=0)
    ventana_inicia = models.DateTimeField()
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Intentos: {self.intentos}"


class ItemCarrito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items_carrito",
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.CASCADE,
        related_name="items_carrito",
    )
    cantidad = models.PositiveIntegerField(default=1)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "producto"],
                name="carrito_usuario_producto_unico",
            ),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.usuario.username}: {self.producto} x {self.cantidad}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PAGADO = "pagado", "Pagado"
        PREPARANDO = "preparando", "Preparando"
        ENVIADO = "enviado", "Enviado"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    numero = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PAGADO,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    destinatario = models.CharField(max_length=150, default="")
    telefono_envio = models.CharField(max_length=20, default="")
    direccion_envio = models.CharField(max_length=255, default="")
    ciudad_envio = models.CharField(max_length=100, default="")
    departamento_envio = models.CharField(max_length=100, default="")
    codigo_postal_envio = models.CharField(max_length=20, blank=True, default="")
    instrucciones_envio = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-creado_en", "-id"]

    def __str__(self):
        return f"Pedido {str(self.numero)[:8]} - {self.usuario.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_pedido",
    )
    nombre_producto = models.CharField(max_length=150)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.nombre_producto} x {self.cantidad}"
