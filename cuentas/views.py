from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import (
    csrf_protect,
    ensure_csrf_cookie,
)

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def obtener_csrf(request):
    """
    Genera una cookie CSRF y devuelve el token al frontend.
    """

    return Response({
        "csrfToken": get_token(request),
    })


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def iniciar_sesion(request):
    """
    Autentica exclusivamente usuarios administradores.
    """

    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {
                "detail": (
                    "El usuario y la contraseña "
                    "son obligatorios."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    usuario = authenticate(
        request=request,
        username=username,
        password=password,
    )

    if usuario is None:
        return Response(
            {
                "detail": (
                    "El usuario o la contraseña "
                    "son incorrectos."
                )
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not usuario.is_active:
        return Response(
            {
                "detail": "La cuenta está desactivada."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if not usuario.is_staff:
        return Response(
            {
                "detail": (
                    "La cuenta no tiene permisos "
                    "administrativos."
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    login(request, usuario)

    # Django rota el token CSRF después del login.
    token_csrf = get_token(request)

    return Response({
        "detail": "Sesión iniciada correctamente.",
        "csrfToken": token_csrf,
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "isStaff": usuario.is_staff,
        },
    })


@csrf_protect
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cerrar_sesion(request):
    """
    Cierra la sesión del administrador autenticado.
    """

    logout(request)

    return Response({
        "detail": "Sesión cerrada correctamente.",
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def consultar_sesion(request):
    """
    Informa al frontend si existe una sesión activa.
    """

    if not request.user.is_authenticated:
        return Response({
            "autenticado": False,
            "usuario": None,
        })

    return Response({
        "autenticado": True,
        "usuario": {
            "id": request.user.id,
            "username": request.user.username,
            "isStaff": request.user.is_staff,
        },
    })