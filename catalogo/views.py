from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Categoria, Producto
from .permissions import EsAdministradorOConsulta
from .serializers import (
    CategoriaSerializer,
    ProductoSerializer,
)


class CategoriaViewSet(ModelViewSet):
    queryset = Categoria.objects.prefetch_related(
        "productos"
    ).all()

    serializer_class = CategoriaSerializer
    permission_classes = [
        EsAdministradorOConsulta,
    ]

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()

        cantidad_productos = (
            categoria.productos.count()
        )

        if cantidad_productos > 0:
            return Response(
                {
                    "detail": (
                        "No se puede eliminar esta categoría "
                        f"porque tiene {cantidad_productos} "
                        "producto(s) asociado(s)."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_destroy(categoria)

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ProductoViewSet(ModelViewSet):
    """
    CRUD de productos.

    Las consultas son públicas.
    Las modificaciones requieren administrador.
    """

    serializer_class = ProductoSerializer
    permission_classes = [
        EsAdministradorOConsulta,
    ]

    def get_queryset(self):
        queryset = Producto.objects.select_related(
            "categoria"
        ).all()

        categoria_id = self.request.query_params.get(
            "categoria"
        )

        busqueda = self.request.query_params.get(
            "buscar"
        )

        if categoria_id:
            queryset = queryset.filter(
                categoria_id=categoria_id
            )

        if busqueda:
            queryset = queryset.filter(
                nombre__icontains=busqueda.strip()
            )

        return queryset
