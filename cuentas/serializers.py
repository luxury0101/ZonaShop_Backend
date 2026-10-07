from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import ItemCarrito, ItemPedido, Pedido, PerfilUsuario


Usuario = get_user_model()


def obtener_rol(usuario):
    rol_predeterminado = (
        PerfilUsuario.Rol.ADMINISTRADOR
        if usuario.is_staff or usuario.is_superuser
        else PerfilUsuario.Rol.CLIENTE
    )
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=usuario,
        defaults={"rol": rol_predeterminado},
    )
    return perfil.rol


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class CsrfTokenSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()


class RegistroUsuarioSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    passwordConfirmacion = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate_nombre(self, nombre):
        nombre = " ".join(nombre.split())
        if len(nombre) < 2:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 2 caracteres."
            )
        return nombre

    def validate_email(self, email):
        email = email.strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Ya existe una cuenta con este correo."
            )
        return email

    def validate(self, datos):
        if datos["password"] != datos["passwordConfirmacion"]:
            raise serializers.ValidationError({
                "passwordConfirmacion": "Las contraseñas no coinciden.",
            })
        validate_password(datos["password"])
        return datos

    def create(self, datos):
        datos.pop("passwordConfirmacion")
        nombre = datos.pop("nombre")
        email = datos.pop("email")
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            first_name=nombre,
            password=datos.pop("password"),
        )
        PerfilUsuario.objects.create(
            usuario=usuario,
            rol=PerfilUsuario.Rol.CLIENTE,
        )
        return usuario


class CredencialesSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=254, required=False)
    username = serializers.CharField(max_length=254, required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, datos):
        identificador = datos.get("email") or datos.get("username")
        if not identificador:
            raise serializers.ValidationError({
                "email": "El correo es obligatorio.",
            })
        datos["identificador"] = identificador
        return datos


class UsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    email = serializers.EmailField()
    rol = serializers.ChoiceField(choices=PerfilUsuario.Rol.choices)


class InicioSesionSerializer(serializers.Serializer):
    detail = serializers.CharField()
    csrfToken = serializers.CharField()
    usuario = UsuarioSerializer()


class CierreSesionSerializer(serializers.Serializer):
    detail = serializers.CharField()


class EstadoSesionSerializer(serializers.Serializer):
    autenticado = serializers.BooleanField()
    usuario = UsuarioSerializer(allow_null=True, required=False)


class ItemCarritoEntradaSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class FusionCarritoSerializer(serializers.Serializer):
    items = ItemCarritoEntradaSerializer(many=True)
    fusionar = serializers.BooleanField(default=False)


class ItemCarritoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="producto.id")
    nombre = serializers.CharField(source="producto.nombre")
    precio = serializers.DecimalField(
        source="producto.precio",
        max_digits=12,
        decimal_places=2,
    )
    existencias = serializers.IntegerField(source="producto.existencias")
    imagen = serializers.ImageField(
        source="producto.imagen",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ItemCarrito
        fields = [
            "id",
            "nombre",
            "precio",
            "existencias",
            "cantidad",
            "imagen",
        ]


class CompraSimuladaSerializer(serializers.Serializer):
    items = ItemCarritoEntradaSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("El carrito está vacío.")

        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "El carrito contiene productos duplicados."
            )
        return items


class ItemPedidoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ItemPedido
        fields = [
            "producto_id",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = ["numero", "total", "estado", "creado_en", "items"]
