from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        max_length=2000,
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
        max_length=4000,
        blank=True,
        default="",
    )

    imagen = models.ImageField(
        upload_to="productos/",
        max_length=500,
        blank=True,
        null=True,
    )

    imagen_secundaria = models.ImageField(
        upload_to="productos/",
        max_length=500,
        blank=True,
        null=True,
    )

    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    existencias = models.PositiveIntegerField(
        default=0,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        null=True,
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

    def stock_para_talla(self, talla=""):
        tallas = list(self.tallas.all())
        if not tallas:
            return self.existencias if not talla else 0
        if not talla:
            return 0
        return next(
            (item.stock for item in tallas if item.talla == talla),
            0,
        )


class TallaProducto(models.Model):
    class Talla(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="tallas",
    )
    talla = models.CharField(max_length=2, choices=Talla.choices)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "talla"],
                name="producto_talla_unica",
            ),
        ]

    def __str__(self):
        return f"{self.producto} · {self.talla}: {self.stock}"
