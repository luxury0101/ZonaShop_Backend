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
