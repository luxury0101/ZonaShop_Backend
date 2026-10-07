from rest_framework.permissions import BasePermission

from .models import PerfilUsuario
from .serializers import obtener_rol


class EsAdministrador(BasePermission):
    message = "No tienes permisos para administrar pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and obtener_rol(request.user) == PerfilUsuario.Rol.ADMINISTRADOR
        )
