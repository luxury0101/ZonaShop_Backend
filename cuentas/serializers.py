from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalogo.models import TallaProducto
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
    talla = serializers.ChoiceField(
        choices=TallaProducto.Talla.choices,
        allow_blank=True,
        default="",
    )


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
    existencias = serializers.SerializerMethodField()
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
            "talla",
            "imagen",
        ]

    def get_existencias(self, objeto) -> int:
        return objeto.producto.stock_para_talla(objeto.talla)


class CompraSimuladaSerializer(serializers.Serializer):
    items = ItemCarritoEntradaSerializer(many=True)
    envio = serializers.DictField()
    guardarDireccion = serializers.BooleanField(default=False)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("El carrito está vacío.")

        claves = [(item["id"], item.get("talla", "")) for item in items]
        if len(claves) != len(set(claves)):
            raise serializers.ValidationError(
                "El carrito contiene productos duplicados."
            )
        return items

    def validate_envio(self, envio):
        serializer = DatosEnvioSerializer(data=envio)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class DatosEnvioSerializer(serializers.Serializer):
    destinatario = serializers.CharField(min_length=2, max_length=150)
    telefono = serializers.RegexField(
        regex=r"^[0-9+()\-\s]{7,20}$",
        error_messages={"invalid": "Escribe un teléfono válido."},
    )
    direccion = serializers.CharField(min_length=5, max_length=255)
    ciudad = serializers.CharField(min_length=2, max_length=100)
    departamento = serializers.CharField(min_length=2, max_length=100)
    codigo_postal = serializers.CharField(max_length=20, allow_blank=True, default="")
    instrucciones = serializers.CharField(max_length=500, allow_blank=True, default="")


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="usuario.first_name", min_length=2, max_length=150)
    email = serializers.EmailField(source="usuario.email", max_length=254)
    passwordActual = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )
    passwordNueva = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )
    passwordConfirmacion = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            "nombre",
            "email",
            "telefono",
            "direccion",
            "ciudad",
            "departamento",
            "codigo_postal",
            "instrucciones_envio",
            "passwordActual",
            "passwordNueva",
            "passwordConfirmacion",
        ]

    def validate_email(self, email):
        usuario = self.instance.usuario
        correo_ocupado = Usuario.objects.filter(email__iexact=email).exclude(
            pk=usuario.pk
        ).exists()
        usuario_ocupado = Usuario.objects.filter(username__iexact=email).exclude(
            pk=usuario.pk
        ).exists()
        if correo_ocupado or usuario_ocupado:
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return email.strip().lower()

    def validate(self, datos):
        actual = datos.get("passwordActual", "")
        nueva = datos.get("passwordNueva", "")
        confirmacion = datos.get("passwordConfirmacion", "")
        if actual or nueva or confirmacion:
            if not actual:
                raise serializers.ValidationError({
                    "passwordActual": "Escribe tu contraseña actual."
                })
            if not self.instance.usuario.check_password(actual):
                raise serializers.ValidationError({
                    "passwordActual": "La contraseña actual es incorrecta."
                })
            if nueva != confirmacion:
                raise serializers.ValidationError({
                    "passwordConfirmacion": "Las contraseñas no coinciden."
                })
            validate_password(nueva, self.instance.usuario)
        return datos

    def update(self, perfil, datos):
        datos_usuario = datos.pop("usuario", {})
        password_nueva = datos.pop("passwordNueva", "")
        datos.pop("passwordActual", None)
        datos.pop("passwordConfirmacion", None)
        usuario = perfil.usuario
        email_anterior = usuario.email
        usuario.first_name = datos_usuario.get("first_name", usuario.first_name)
        usuario.email = datos_usuario.get("email", usuario.email)
        if usuario.username.lower() == email_anterior.lower():
            usuario.username = usuario.email
        if password_nueva:
            usuario.set_password(password_nueva)
        usuario.save()
        for campo, valor in datos.items():
            setattr(perfil, campo, valor)
        perfil.save()
        return perfil


class ItemPedidoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ItemPedido
        fields = [
            "producto_id",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "talla",
            "subtotal",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    envio = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = ["numero", "total", "estado", "creado_en", "envio", "items"]

    @extend_schema_field(DatosEnvioSerializer)
    def get_envio(self, pedido):
        return {
            "destinatario": pedido.destinatario,
            "telefono": pedido.telefono_envio,
            "direccion": pedido.direccion_envio,
            "ciudad": pedido.ciudad_envio,
            "departamento": pedido.departamento_envio,
            "codigo_postal": pedido.codigo_postal_envio,
            "instrucciones": pedido.instrucciones_envio,
        }


class PedidoAdministradorSerializer(PedidoSerializer):
    cliente = serializers.SerializerMethodField()

    class Meta(PedidoSerializer.Meta):
        fields = PedidoSerializer.Meta.fields + ["cliente"]

    @extend_schema_field({
        "type": "object",
        "properties": {
            "nombre": {"type": "string"},
            "email": {"type": "string", "format": "email"},
        },
    })
    def get_cliente(self, pedido):
        return {
            "nombre": pedido.usuario.get_full_name().strip() or pedido.usuario.username,
            "email": pedido.usuario.email or pedido.usuario.username,
        }


class EstadoPedidoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Pedido.Estado.choices)
