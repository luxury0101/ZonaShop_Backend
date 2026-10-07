from datetime import timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalogo.models import Producto

from .models import IntentoInicioSesion, ItemCarrito, ItemPedido, Pedido, PerfilUsuario
from .permissions import EsAdministrador
from .serializers import (
    CierreSesionSerializer,
    CompraSimuladaSerializer,
    CredencialesSerializer,
    CsrfTokenSerializer,
    ErrorSerializer,
    EstadoSesionSerializer,
    FusionCarritoSerializer,
    InicioSesionSerializer,
    ItemCarritoSerializer,
    PedidoSerializer,
    PedidoAdministradorSerializer,
    PerfilUsuarioSerializer,
    RegistroUsuarioSerializer,
    EstadoPedidoSerializer,
    obtener_rol,
)


Usuario = get_user_model()


def datos_usuario(usuario):
    return {
        "id": usuario.id,
        "nombre": usuario.get_full_name().strip() or usuario.username,
        "email": usuario.email or usuario.username,
        "rol": obtener_rol(usuario),
    }


def clave_intentos(request, identificador):
    ip = request.META.get("REMOTE_ADDR", "sin-ip")
    valor = f"{identificador.strip().lower()}|{ip}"
    return salted_hmac("zonashop.login", valor).hexdigest()


def segundos_bloqueo(clave):
    intento = IntentoInicioSesion.objects.filter(clave=clave).first()
    if intento and intento.bloqueado_hasta:
        restantes = ceil((intento.bloqueado_hasta - timezone.now()).total_seconds())
        return max(restantes, 0)
    return 0


@transaction.atomic
def registrar_fallo(clave):
    ahora = timezone.now()
    ventana = timedelta(seconds=settings.LOGIN_ATTEMPT_WINDOW_SECONDS)
    bloqueo = timedelta(seconds=settings.LOGIN_BLOCK_SECONDS)
    intento, _ = IntentoInicioSesion.objects.select_for_update().get_or_create(
        clave=clave,
        defaults={"ventana_inicia": ahora},
    )
    if ahora - intento.ventana_inicia >= ventana:
        intento.intentos = 0
        intento.ventana_inicia = ahora
        intento.bloqueado_hasta = None
    intento.intentos += 1
    if intento.intentos >= settings.LOGIN_MAX_ATTEMPTS:
        intento.bloqueado_hasta = ahora + bloqueo
    intento.save()


@extend_schema(summary="Obtener token CSRF", responses={200: CsrfTokenSerializer})
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def obtener_csrf(request):
    return Response({"csrfToken": get_token(request)})


@extend_schema(
    summary="Registrar cliente",
    request=RegistroUsuarioSerializer,
    responses={201: InicioSesionSerializer, 400: ErrorSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
@transaction.atomic
def registrar_usuario(request):
    serializer = RegistroUsuarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()
    login(request, usuario)
    return Response(
        {
            "detail": "Cuenta creada correctamente.",
            "csrfToken": get_token(request),
            "usuario": datos_usuario(usuario),
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    summary="Iniciar sesión",
    request=CredencialesSerializer,
    responses={
        200: InicioSesionSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        429: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
def iniciar_sesion(request):
    serializer = CredencialesSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    identificador = serializer.validated_data["identificador"].strip()
    password = serializer.validated_data["password"]
    clave = clave_intentos(request, identificador)
    restantes = segundos_bloqueo(clave)
    if restantes:
        return Response(
            {
                "detail": "Demasiados intentos. Intenta nuevamente más tarde.",
                "retryAfter": restantes,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    candidato = Usuario.objects.filter(email__iexact=identificador).first()
    username = candidato.username if candidato else identificador
    usuario = authenticate(request=request, username=username, password=password)
    if usuario is None or not usuario.is_active:
        registrar_fallo(clave)
        return Response(
            {"detail": "El correo o la contraseña son incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    IntentoInicioSesion.objects.filter(clave=clave).delete()
    login(request, usuario)
    return Response({
        "detail": "Sesión iniciada correctamente.",
        "csrfToken": get_token(request),
        "usuario": datos_usuario(usuario),
    })


@extend_schema(summary="Cerrar sesión", request=None, responses={200: CierreSesionSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_protect
def cerrar_sesion(request):
    logout(request)
    return Response({"detail": "Sesión cerrada correctamente."})


@extend_schema(summary="Consultar sesión", responses={200: EstadoSesionSerializer})
@api_view(["GET"])
@permission_classes([AllowAny])
def consultar_sesion(request):
    if not request.user.is_authenticated:
        return Response({"autenticado": False, "usuario": None})
    return Response({
        "autenticado": True,
        "usuario": datos_usuario(request.user),
    })


@extend_schema(
    summary="Consultar o actualizar el perfil y la dirección principal",
    request=PerfilUsuarioSerializer,
    responses={200: PerfilUsuarioSerializer},
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@csrf_protect
@transaction.atomic
def perfil_usuario(request):
    obtener_rol(request.user)
    perfil = PerfilUsuario.objects.select_related("usuario").get(usuario=request.user)
    if request.method == "PATCH":
        serializer = PerfilUsuarioSerializer(
            perfil,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if serializer.validated_data.get("passwordNueva"):
            update_session_auth_hash(request, perfil.usuario)
    return Response(PerfilUsuarioSerializer(perfil).data)


@extend_schema(
    summary="Consultar o fusionar el carrito del usuario",
    request=FusionCarritoSerializer,
    responses={200: ItemCarritoSerializer(many=True)},
)
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
@csrf_protect
@transaction.atomic
def carrito_usuario(request):
    if request.method == "PUT":
        serializer = FusionCarritoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fusionar = serializer.validated_data["fusionar"]
        cantidades = {}
        for item in serializer.validated_data["items"]:
            cantidades[item["id"]] = cantidades.get(item["id"], 0) + item["cantidad"]
        productos = Producto.objects.filter(id__in=cantidades).in_bulk()
        if not fusionar:
            ItemCarrito.objects.filter(usuario=request.user).exclude(
                producto_id__in=productos,
            ).delete()
        for producto_id, cantidad in cantidades.items():
            producto = productos.get(producto_id)
            if not producto or producto.existencias < 1:
                continue
            item, creado = ItemCarrito.objects.select_for_update().get_or_create(
                usuario=request.user,
                producto=producto,
                defaults={"cantidad": 0},
            )
            base = item.cantidad if fusionar and not creado else 0
            item.cantidad = min(base + cantidad, producto.existencias)
            item.save()

    items = list(
        ItemCarrito.objects.filter(usuario=request.user).select_related("producto")
    )
    items_validos = []
    for item in items:
        if item.producto.existencias < 1:
            item.delete()
            continue
        if item.cantidad > item.producto.existencias:
            item.cantidad = item.producto.existencias
            item.save(update_fields=["cantidad", "actualizado_en"])
        items_validos.append(item)
    return Response(
        ItemCarritoSerializer(
            items_validos,
            many=True,
            context={"request": request},
        ).data
    )


@extend_schema(
    summary="Listar pedidos o completar una compra simulada",
    request=CompraSimuladaSerializer,
    responses={200: PedidoSerializer(many=True), 201: PedidoSerializer},
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@csrf_protect
@transaction.atomic
def pedidos_usuario(request):
    if request.method == "GET":
        pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related(
            "items"
        )
        return Response(PedidoSerializer(pedidos, many=True).data)

    serializer = CompraSimuladaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cantidades = {
        item["id"]: item["cantidad"]
        for item in serializer.validated_data["items"]
    }
    envio = serializer.validated_data["envio"]

    productos = {
        producto.id: producto
        for producto in Producto.objects.select_for_update()
        .filter(id__in=cantidades)
        .order_by("id")
    }
    faltantes = set(cantidades) - set(productos)
    if faltantes:
        return Response(
            {"detail": "Uno de los productos ya no está disponible."},
            status=status.HTTP_409_CONFLICT,
        )

    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        if producto.existencias < cantidad:
            return Response(
                {
                    "detail": (
                        f"No hay stock suficiente de {producto.nombre}. "
                        f"Solo quedan {producto.existencias} unidades disponibles."
                    ),
                    "producto": producto.nombre,
                    "disponibles": producto.existencias,
                },
                status=status.HTTP_409_CONFLICT,
            )

    total = sum(
        productos[producto_id].precio * cantidad
        for producto_id, cantidad in cantidades.items()
    )
    pedido = Pedido.objects.create(
        usuario=request.user,
        total=total,
        estado=Pedido.Estado.PAGADO,
        destinatario=envio["destinatario"],
        telefono_envio=envio["telefono"],
        direccion_envio=envio["direccion"],
        ciudad_envio=envio["ciudad"],
        departamento_envio=envio["departamento"],
        codigo_postal_envio=envio.get("codigo_postal", ""),
        instrucciones_envio=envio.get("instrucciones", ""),
    )

    if serializer.validated_data["guardarDireccion"]:
        obtener_rol(request.user)
        perfil = request.user.perfil_zonashop
        perfil.telefono = envio["telefono"]
        perfil.direccion = envio["direccion"]
        perfil.ciudad = envio["ciudad"]
        perfil.departamento = envio["departamento"]
        perfil.codigo_postal = envio.get("codigo_postal", "")
        perfil.instrucciones_envio = envio.get("instrucciones", "")
        perfil.save()

    items_pedido = []
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        subtotal = producto.precio * cantidad
        items_pedido.append(
            ItemPedido(
                pedido=pedido,
                producto=producto,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=cantidad,
                subtotal=subtotal,
            )
        )
        producto.existencias -= cantidad
        producto.save(update_fields=["existencias"])

    ItemPedido.objects.bulk_create(items_pedido)
    ItemCarrito.objects.filter(usuario=request.user).delete()

    # Aquí se confirmaría el pago con Stripe, Mercado Pago, Wompi o PayU.
    # Este endpoint no recibe ni almacena números de tarjeta o códigos CVV.
    pedido = Pedido.objects.prefetch_related("items").get(pk=pedido.pk)
    return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Listar todos los pedidos para administración",
    responses={200: PedidoAdministradorSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([EsAdministrador])
def pedidos_administracion(request):
    pedidos = Pedido.objects.select_related("usuario").prefetch_related("items")
    estado_filtro = request.query_params.get("estado", "").strip()
    if estado_filtro:
        estados_validos = {valor for valor, _ in Pedido.Estado.choices}
        if estado_filtro not in estados_validos:
            return Response(
                {"detail": "El estado indicado no es válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedidos = pedidos.filter(estado=estado_filtro)
    return Response(PedidoAdministradorSerializer(pedidos, many=True).data)


@extend_schema(
    summary="Actualizar el estado de un pedido",
    request=EstadoPedidoSerializer,
    responses={200: PedidoAdministradorSerializer},
)
@api_view(["PATCH"])
@permission_classes([EsAdministrador])
@csrf_protect
def actualizar_estado_pedido(request, numero):
    try:
        pedido = Pedido.objects.select_related("usuario").prefetch_related("items").get(
            numero=numero
        )
    except Pedido.DoesNotExist:
        return Response(
            {"detail": "El pedido no existe."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = EstadoPedidoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    pedido.estado = serializer.validated_data["estado"]
    pedido.save(update_fields=["estado"])
    return Response(PedidoAdministradorSerializer(pedido).data)
