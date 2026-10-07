from django.contrib import admin

from .models import (
    IntentoInicioSesion,
    ItemCarrito,
    ItemPedido,
    Pedido,
    PerfilUsuario,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol")
    list_filter = ("rol",)
    search_fields = ("usuario__username", "usuario__email")


@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "producto", "cantidad", "actualizado_en")
    search_fields = ("usuario__email", "producto__nombre")


@admin.register(IntentoInicioSesion)
class IntentoInicioSesionAdmin(admin.ModelAdmin):
    list_display = ("intentos", "ventana_inicia", "bloqueado_hasta")
    readonly_fields = ("clave", "intentos", "ventana_inicia", "bloqueado_hasta")


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = (
        "producto",
        "nombre_producto",
        "precio_unitario",
        "cantidad",
        "subtotal",
    )


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "usuario", "total", "estado", "creado_en")
    list_filter = ("estado", "creado_en")
    search_fields = ("numero", "usuario__email")
    readonly_fields = ("numero", "usuario", "total", "estado", "creado_en")
    inlines = [ItemPedidoInline]
