from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class CsrfTokenSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()


class CredencialesSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UsuarioAdministradorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    isStaff = serializers.BooleanField()


class InicioSesionSerializer(serializers.Serializer):
    detail = serializers.CharField()
    csrfToken = serializers.CharField()
    usuario = UsuarioAdministradorSerializer()


class CierreSesionSerializer(serializers.Serializer):
    detail = serializers.CharField()


class EstadoSesionSerializer(serializers.Serializer):
    autenticado = serializers.BooleanField()
    usuario = UsuarioAdministradorSerializer(
        allow_null=True,
        required=False,
    )
