from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Direccion
from .serializers import DireccionSerializer, RegistroClienteSerializer


def datos_usuario(usuario):
    perfil = getattr(usuario, "perfil_cliente", None)
    return {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.first_name,
        "apellido": usuario.last_name,
        "telefono": perfil.telefono if perfil else "",
        "isStaff": usuario.is_staff,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def registrar_cliente(request):
    serializer = RegistroClienteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()
    login(request, usuario)
    return Response(
        {"usuario": datos_usuario(usuario)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def iniciar_sesion_cliente(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    usuario = authenticate(
        request=request,
        username=email,
        password=password,
    )
    if usuario is None or not usuario.is_active:
        return Response(
            {"detail": "Correo o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    login(request, usuario)
    return Response({"usuario": datos_usuario(usuario)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cerrar_sesion_cliente(request):
    logout(request)
    return Response({"detail": "Sesión cerrada correctamente."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_cuenta(request):
    return Response({"usuario": datos_usuario(request.user)})


class DireccionViewSet(ModelViewSet):
    serializer_class = DireccionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Direccion.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
