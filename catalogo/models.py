from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )

    nombre = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField(
        blank=True,
        default="",
    )

    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    existencias = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"
        indexes = [
            models.Index(
                fields=["categoria", "nombre"],
                name="producto_cat_nombre_idx",
            )
        ]

    def __str__(self):
        return self.nombre

    @property
    def agotado(self):
        return self.existencias == 0