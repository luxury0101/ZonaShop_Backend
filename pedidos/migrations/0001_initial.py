from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogo", "0002_producto_imagen"),
        ("clientes", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("referencia", models.CharField(max_length=64, unique=True)),
                ("estado", models.CharField(choices=[("PENDIENTE_PAGO", "Pendiente de pago"), ("CONFIRMADO", "Confirmado"), ("PAGO_RECHAZADO", "Pago rechazado"), ("CANCELADO", "Cancelado")], default="PENDIENTE_PAGO", max_length=30)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("expira_en", models.DateTimeField()),
                ("inventario_liberado", models.BooleanField(default=False)),
                ("direccion", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="clientes.direccion")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-creado_en"]},
        ),
        migrations.CreateModel(
            name="DetallePedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre_producto", models.CharField(max_length=150)),
                ("precio_unitario", models.DecimalField(decimal_places=2, max_digits=12)),
                ("cantidad", models.PositiveIntegerField()),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=12)),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detalles", to="pedidos.pedido")),
                ("producto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="detalles_pedido", to="catalogo.producto")),
            ],
        ),
        migrations.CreateModel(
            name="Pago",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proveedor", models.CharField(default="WOMPI", max_length=30)),
                ("transaccion_id", models.CharField(blank=True, default="", max_length=100)),
                ("estado", models.CharField(default="PENDING", max_length=30)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("pedido", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pago", to="pedidos.pedido")),
            ],
        ),
    ]
