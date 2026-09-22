import hashlib
import hmac
import uuid
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalogo.models import Producto
from clientes.models import Direccion
from .models import DetallePedido, Pago, Pedido
from .serializers import PedidoSerializer


def valor_anidado(datos, ruta):
    valor = datos
    for parte in ruta.split("."):
        valor = valor[parte]
    return valor


def liberar_inventario(pedido):
    if pedido.inventario_liberado:
        return
    for detalle in pedido.detalles.select_related("producto"):
        Producto.objects.filter(pk=detalle.producto_id).update(
            existencias=models.F("existencias") + detalle.cantidad
        )
    pedido.inventario_liberado = True
    pedido.save(update_fields=["inventario_liberado"])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_pedidos(request):
    pedidos = Pedido.objects.filter(
        usuario=request.user
    ).prefetch_related("detalles").select_related("pago", "direccion")
    return Response(PedidoSerializer(pedidos, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def crear_checkout(request):
    public_key = settings.WOMPI_PUBLIC_KEY
    integrity_secret = settings.WOMPI_INTEGRITY_SECRET

    if not public_key or not integrity_secret:
        return Response(
            {"detail": "Wompi Sandbox aún no está configurado."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        direccion = Direccion.objects.get(
            pk=request.data.get("direccion"),
            usuario=request.user,
        )
    except Direccion.DoesNotExist:
        return Response(
            {"detail": "La dirección seleccionada no es válida."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    items = request.data.get("items", [])
    if not isinstance(items, list) or not items:
        return Response(
            {"detail": "El carrito está vacío."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cantidades = {}
    for item in items:
        producto_id = str(item.get("producto", ""))
        cantidad = item.get("cantidad")
        if not producto_id or not isinstance(cantidad, int) or cantidad < 1:
            return Response(
                {"detail": "Hay productos o cantidades inválidas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

    productos = {
        str(producto.id): producto
        for producto in Producto.objects.select_for_update().filter(
            id__in=cantidades.keys()
        )
    }

    if len(productos) != len(cantidades):
        return Response(
            {"detail": "Uno de los productos ya no existe."},
            status=status.HTTP_409_CONFLICT,
        )

    total = Decimal("0.00")
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        if producto.existencias < cantidad:
            return Response(
                {
                    "detail": (
                        f"No hay existencias suficientes de {producto.nombre}."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        total += producto.precio * cantidad

    referencia = f"ZS-{uuid.uuid4().hex.upper()}"
    expira_en = timezone.now() + timedelta(minutes=30)

    pedido = Pedido.objects.create(
        usuario=request.user,
        direccion=direccion,
        referencia=referencia,
        total=total,
        expira_en=expira_en,
    )

    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        Producto.objects.filter(pk=producto.pk).update(
            existencias=models.F("existencias") - cantidad
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            precio_unitario=producto.precio,
            cantidad=cantidad,
            subtotal=producto.precio * cantidad,
        )

    Pago.objects.create(pedido=pedido)

    monto_centavos = int(total * 100)
    expiracion = expira_en.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    cadena = (
        f"{referencia}{monto_centavos}COP"
        f"{expiracion}{integrity_secret}"
    )
    firma = hashlib.sha256(cadena.encode("utf-8")).hexdigest()

    parametros = {
        "public-key": public_key,
        "currency": "COP",
        "amount-in-cents": monto_centavos,
        "reference": referencia,
        "signature:integrity": firma,
        "expiration-time": expiracion,
        "redirect-url": settings.WOMPI_REDIRECT_URL,
        "customer-data:email": request.user.email,
        "customer-data:full-name": request.user.get_full_name(),
        "customer-data:phone-number": direccion.telefono,
        "customer-data:phone-number-prefix": "+57",
        "shipping-address:address-line-1": direccion.direccion,
        "shipping-address:address-line-2": direccion.complemento,
        "shipping-address:country": "CO",
        "shipping-address:city": direccion.ciudad,
        "shipping-address:region": direccion.departamento,
        "shipping-address:phone-number": direccion.telefono,
        "shipping-address:name": direccion.destinatario,
    }

    return Response(
        {
            "pedido": PedidoSerializer(pedido).data,
            "checkoutUrl": (
                "https://checkout.wompi.co/p/?" + urlencode(parametros)
            ),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def webhook_wompi(request):
    evento = request.data
    firma = evento.get("signature", {})
    propiedades = firma.get("properties", [])
    secreto = settings.WOMPI_EVENTS_SECRET

    if not secreto:
        return Response(
            {"detail": "Webhook no configurado."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        concatenado = "".join(
            str(valor_anidado(evento["data"], ruta))
            for ruta in propiedades
        )
        concatenado += str(evento["timestamp"]) + secreto
    except (KeyError, TypeError):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    calculado = hashlib.sha256(
        concatenado.encode("utf-8")
    ).hexdigest().upper()
    recibido = str(firma.get("checksum", "")).upper()

    if not hmac.compare_digest(calculado, recibido):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    transaccion = evento.get("data", {}).get("transaction", {})
    try:
        pedido = Pedido.objects.select_for_update().get(
            referencia=transaccion.get("reference")
        )
    except Pedido.DoesNotExist:
        return Response(status=status.HTTP_200_OK)

    if int(pedido.total * 100) != transaccion.get("amount_in_cents"):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    pago = pedido.pago
    pago.transaccion_id = transaccion.get("id", "")
    pago.estado = transaccion.get("status", "UNKNOWN")
    pago.save()

    if pago.estado == "APPROVED":
        pedido.estado = Pedido.Estado.CONFIRMADO
        pedido.save(update_fields=["estado"])
    elif pago.estado in {"DECLINED", "VOIDED", "ERROR"}:
        liberar_inventario(pedido)
        pedido.estado = Pedido.Estado.PAGO_RECHAZADO
        pedido.save(update_fields=["estado"])

    return Response(status=status.HTTP_200_OK)
