from django.conf import settings
from django.db import models


class PerfilCliente(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_cliente",
    )
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class Direccion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="direcciones",
    )
    nombre = models.CharField(max_length=80, default="Principal")
    destinatario = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    departamento = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    complemento = models.CharField(max_length=200, blank=True, default="")
    codigo_postal = models.CharField(max_length=20, blank=True, default="")
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ["-principal", "-id"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.principal:
            Direccion.objects.filter(
                usuario=self.usuario,
                principal=True,
            ).exclude(pk=self.pk).update(principal=False)

    def __str__(self):
        return f"{self.destinatario} - {self.ciudad}"
