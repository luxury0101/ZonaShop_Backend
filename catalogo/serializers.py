from rest_framework import serializers

from .models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    cantidad_productos = serializers.IntegerField(
        source="productos.count",
        read_only=True,
    )

    class Meta:
        model = Categoria

        fields = [
            "id",
            "nombre",
            "descripcion",
            "cantidad_productos",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True,
    )

    agotado = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Producto

        fields = [
            "id",
            "categoria",
            "categoria_nombre",
            "nombre",
            "descripcion",
            "imagen",
            "precio",
            "existencias",
            "agotado",
        ]

    def validate_imagen(self, imagen):
        if imagen is None:
            return imagen

        limite_bytes = 5 * 1024 * 1024

        if imagen.size > limite_bytes:
            raise serializers.ValidationError(
                "La imagen no puede superar los 5 MB."
            )

        tipos_permitidos = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        tipo_contenido = getattr(
            imagen,
            "content_type",
            "",
        )

        if (
            tipo_contenido
            and tipo_contenido not in tipos_permitidos
        ):
            raise serializers.ValidationError(
                "Solo se permiten imágenes JPG, PNG o WEBP."
            )

        return imagen
