from django.contrib import admin

from .models import IntentoInicioSesion, ItemCarrito, PerfilUsuario


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
