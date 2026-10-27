import json

from django.db import transaction
from rest_framework import serializers

from .models import Categoria, Producto, TallaProducto


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


class TallaProductoSerializer(serializers.ModelSerializer):
    agotada = serializers.SerializerMethodField()

    class Meta:
        model = TallaProducto
        fields = ["talla", "stock", "agotada"]

    def get_agotada(self, objeto):
        return objeto.stock == 0


class ListaTallasField(serializers.ListField):
    child = serializers.DictField()

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as error:
                raise serializers.ValidationError(
                    "Las tallas deben tener un formato válido."
                ) from error
        datos = super().to_internal_value(data)
        tallas_validas = set(TallaProducto.Talla.values)
        tallas_vistas = set()
        resultado = []
        validador_stock = serializers.IntegerField(min_value=0)
        for item in datos:
            talla = str(item.get("talla", "")).strip().upper()
            if talla not in tallas_validas:
                raise serializers.ValidationError(
                    f"La talla {talla or 'vacía'} no es válida."
                )
            if talla in tallas_vistas:
                raise serializers.ValidationError(
                    f"La talla {talla} está repetida."
                )
            try:
                stock = validador_stock.run_validation(item.get("stock", 0))
            except serializers.ValidationError as error:
                raise serializers.ValidationError(
                    f"El stock de la talla {talla} debe ser un entero mayor o igual a cero."
                ) from error
            tallas_vistas.add(talla)
            resultado.append({"talla": talla, "stock": stock})
        return resultado

    def to_representation(self, value):
        return TallaProductoSerializer(value.all(), many=True).data


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

    tallas = ListaTallasField(required=False)

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
            "creado_en",
            "agotado",
            "tallas",
        ]

    def _guardar_tallas(self, producto, tallas):
        producto.tallas.all().delete()
        if tallas:
            TallaProducto.objects.bulk_create([
                TallaProducto(producto=producto, **item)
                for item in tallas
            ])
            producto.existencias = sum(item["stock"] for item in tallas)
            producto.save(update_fields=["existencias"])

    @transaction.atomic
    def create(self, validated_data):
        tallas = validated_data.pop("tallas", None)
        producto = super().create(validated_data)
        if tallas is not None:
            self._guardar_tallas(producto, tallas)
        return producto

    @transaction.atomic
    def update(self, instance, validated_data):
        tallas = validated_data.pop("tallas", None)
        if tallas is None and instance.tallas.exists():
            validated_data.pop("existencias", None)
        producto = super().update(instance, validated_data)
        if tallas is not None:
            self._guardar_tallas(producto, tallas)
        return producto

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
