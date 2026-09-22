from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Direccion, PerfilCliente

Usuario = get_user_model()


class RegistroClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    apellido = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telefono = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate_email(self, email):
        email = email.strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Ya existe una cuenta con este correo."
            )
        return email

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        telefono = validated_data.pop("telefono")
        email = validated_data.pop("email")
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data.pop("nombre"),
            last_name=validated_data.pop("apellido"),
            password=validated_data.pop("password"),
        )
        PerfilCliente.objects.create(
            usuario=usuario,
            telefono=telefono,
        )
        return usuario


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        exclude = ["usuario"]
