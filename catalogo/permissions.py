from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)


class EsAdministradorOConsulta(BasePermission):
    """
    Permite consultas públicas.

    Crear, actualizar o eliminar requiere
    un usuario administrador autenticado.
    """

    message = (
        "Se requieren permisos administrativos "
        "para realizar esta operación."
    )

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.user.is_staff
        )