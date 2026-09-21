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
            "precio",
            "existencias",
            "agotado",
        ]