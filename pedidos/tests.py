import hashlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from catalogo.models import Categoria, Producto
from clientes.models import Direccion
from .models import Pedido


@override_settings(
    WOMPI_PUBLIC_KEY="pub_test_demo",
    WOMPI_INTEGRITY_SECRET="integrity_test",
    WOMPI_EVENTS_SECRET="events_test",
)
class CheckoutInventarioTests(APITestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="cliente@zonashop.test",
            email="cliente@zonashop.test",
            password="PruebaSegura123!",
        )
        self.direccion = Direccion.objects.create(
            usuario=self.usuario,
            destinatario="Cliente Prueba",
            telefono="3001234567",
            departamento="Santander",
            ciudad="Bucaramanga",
            direccion="Calle 1 # 2-3",
            principal=True,
        )
        categoria = Categoria.objects.create(nombre="Camisetas")
        self.producto = Producto.objects.create(
            categoria=categoria,
            nombre="Camiseta de prueba",
            precio="50000.00",
            existencias=5,
        )
        self.client.force_authenticate(self.usuario)

    def crear_pedido(self):
        return self.client.post(
            "/api/pedidos/checkout/",
            {
                "direccion": self.direccion.id,
                "items": [{"producto": self.producto.id, "cantidad": 2}],
            },
            format="json",
        )

    def test_checkout_reserva_inventario_y_calcula_total_en_backend(self):
        respuesta = self.crear_pedido()
        self.assertEqual(respuesta.status_code, 201)
        self.producto.refresh_from_db()
        pedido = Pedido.objects.get()
        self.assertEqual(self.producto.existencias, 3)
        self.assertEqual(str(pedido.total), "100000.00")
        self.assertIn("checkout.wompi.co", respuesta.data["checkoutUrl"])

    def test_pedido_expirado_libera_inventario_una_sola_vez(self):
        self.crear_pedido()
        pedido = Pedido.objects.get()
        pedido.expira_en = timezone.now() - timedelta(seconds=1)
        pedido.save(update_fields=["expira_en"])
        self.client.get("/api/pedidos/")
        self.client.get("/api/pedidos/")
        pedido.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.CANCELADO)
        self.assertTrue(pedido.inventario_liberado)
        self.assertEqual(self.producto.existencias, 5)

    def test_webhook_rechazado_libera_inventario(self):
        self.crear_pedido()
        pedido = Pedido.objects.get()
        transaccion = {
            "id": "test-transaction",
            "reference": pedido.referencia,
            "amount_in_cents": 10000000,
            "currency": "COP",
            "status": "DECLINED",
        }
        timestamp = 1234567890
        propiedades = [
            "transaction.id",
            "transaction.status",
            "transaction.amount_in_cents",
        ]
        concatenado = (
            f"{transaccion['id']}{transaccion['status']}"
            f"{transaccion['amount_in_cents']}{timestamp}events_test"
        )
        checksum = hashlib.sha256(concatenado.encode()).hexdigest()
        self.client.force_authenticate(user=None)
        respuesta = self.client.post(
            "/api/pedidos/wompi/webhook/",
            {
                "event": "transaction.updated",
                "data": {"transaction": transaccion},
                "timestamp": timestamp,
                "signature": {
                    "properties": propiedades,
                    "checksum": checksum,
                },
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 200)
        pedido.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.PAGO_RECHAZADO)
        self.assertEqual(self.producto.existencias, 5)
