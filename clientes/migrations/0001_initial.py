from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="PerfilCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telefono", models.CharField(max_length=20)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_cliente", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Direccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(default="Principal", max_length=80)),
                ("destinatario", models.CharField(max_length=150)),
                ("telefono", models.CharField(max_length=20)),
                ("departamento", models.CharField(max_length=100)),
                ("ciudad", models.CharField(max_length=100)),
                ("direccion", models.CharField(max_length=200)),
                ("complemento", models.CharField(blank=True, default="", max_length=200)),
                ("codigo_postal", models.CharField(blank=True, default="", max_length=20)),
                ("principal", models.BooleanField(default=False)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="direcciones", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-principal", "-id"]},
        ),
    ]
