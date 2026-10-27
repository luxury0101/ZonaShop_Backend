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
        # MultiPartParser entrega un único valor de FormData como una lista
        # de una cadena. Normalizamos ese caso antes de validar cada talla.
        if (
            isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], str)
        ):
            data = data[0]
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

    imagen_secundaria = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    existencias = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=2147483647,
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
            "imagen_secundaria",
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

    def validate(self, attrs):
        tallas = attrs.get("tallas")
        if self.instance is None and tallas is None and "existencias" not in attrs:
            raise serializers.ValidationError({
                "existencias": "Indica las existencias o el stock por talla.",
            })
        if tallas is not None:
            total = sum(item["stock"] for item in tallas)
            if total > 2147483647:
                raise serializers.ValidationError({
                    "tallas": "El stock total supera el máximo permitido.",
                })
        return attrs

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

    def _validar_imagen(self, imagen):
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

    def validate_imagen(self, imagen):
        return self._validar_imagen(imagen)

    def validate_imagen_secundaria(self, imagen):
        return self._validar_imagen(imagen)
