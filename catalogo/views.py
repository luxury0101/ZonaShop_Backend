from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Categoria, Producto
from .serializers import CategoriaSerializer, ProductoSerializer


class CategoriaViewSet(ReadOnlyModelViewSet):
    queryset = Categoria.objects.prefetch_related(
        "productos"
    ).all()

    serializer_class = CategoriaSerializer


class ProductoViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductoSerializer

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