from django.contrib import admin

from .models import Categoria, Producto, TallaProducto


class TallaProductoInline(admin.TabularInline):
    model = TallaProducto
    extra = 0
    max_num = 5


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
    inlines = [TallaProductoInline]
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

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is TallaProducto and form.instance.tallas.exists():
            form.instance.existencias = sum(
                talla.stock for talla in form.instance.tallas.all()
            )
            form.instance.save(update_fields=["existencias"])

    esta_agotado.boolean = True
    esta_agotado.short_description = "Agotado"
