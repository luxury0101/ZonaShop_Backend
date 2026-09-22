from rest_framework import serializers

from .models import DetallePedido, Pago, Pedido


class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = [
            "producto",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal",
        ]


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = ["proveedor", "transaccion_id", "estado"]


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    pago = PagoSerializer(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "referencia",
            "estado",
            "total",
            "creado_en",
            "expira_en",
            "direccion",
            "detalles",
            "pago",
        ]
