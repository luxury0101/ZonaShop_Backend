from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "cantidad_productos",
    )

    search_fields = (
        "nombre",
    )

    def cantidad_productos(self, obj):
        return obj.productos.count()

    cantidad_productos.short_description = "Productos"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "categoria",
        "precio",
        "existencias",
        "esta_agotado",
    )

    list_filter = (
        "categoria",
    )

    search_fields = (
        "nombre",
        "descripcion",
    )

    list_select_related = (
        "categoria",
    )

    def esta_agotado(self, obj):
        return obj.agotado

    esta_agotado.boolean = True
    esta_agotado.short_description = "Agotado"