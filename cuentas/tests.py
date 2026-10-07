from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from catalogo.models import Categoria, Producto

from .models import ItemCarrito, PerfilUsuario


class AutenticacionApiTests(APITestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_user(
            username="admin",
            email="admin@zonashop.test",
            password="clave-segura",
            is_staff=True,
        )
        self.usuario = get_user_model().objects.create_user(
            username="cliente@zonashop.test",
            email="cliente@zonashop.test",
            first_name="Cliente",
            password="clave-segura",
        )

    def cliente_con_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        respuesta = cliente.get(reverse("cuentas:obtener-csrf"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return cliente, respuesta.data["csrfToken"]

    def test_registro_crea_cliente_con_password_hasheado_y_sesion(self):
        cliente, token = self.cliente_con_csrf()
        respuesta = cliente.post(
            reverse("cuentas:registro"),
            {
                "nombre": "Ana Pérez",
                "email": "ANA@EXAMPLE.COM",
                "password": "ClaveSegura2026!",
                "passwordConfirmacion": "ClaveSegura2026!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["usuario"]["rol"], "cliente")
        usuario = get_user_model().objects.get(email="ana@example.com")
        self.assertNotEqual(usuario.password, "ClaveSegura2026!")
        self.assertTrue(usuario.check_password("ClaveSegura2026!"))
        self.assertEqual(usuario.perfil_zonashop.rol, PerfilUsuario.Rol.CLIENTE)
        self.assertTrue(cliente.get(reverse("cuentas:consultar-sesion")).data["autenticado"])

    def test_registro_valida_correo_y_confirmacion(self):
        cliente, token = self.cliente_con_csrf()
        respuesta = cliente.post(
            reverse("cuentas:registro"),
            {
                "nombre": "Ana",
                "email": self.usuario.email,
                "password": "ClaveSegura2026!",
                "passwordConfirmacion": "otra",
            },
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cliente_y_administrador_inician_sesion_por_el_mismo_endpoint(self):
        for email, rol in [
            (self.usuario.email, "cliente"),
            (self.administrador.email, "administrador"),
        ]:
            with self.subTest(email=email):
                cliente, token = self.cliente_con_csrf()
                respuesta = cliente.post(
                    reverse("cuentas:iniciar-sesion"),
                    {"email": email, "password": "clave-segura"},
                    format="json",
                    HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
                self.assertEqual(respuesta.data["usuario"]["rol"], rol)

    def test_login_se_bloquea_tras_cinco_fallos(self):
        cliente, token = self.cliente_con_csrf()
        for _ in range(5):
            respuesta = cliente.post(
                reverse("cuentas:iniciar-sesion"),
                {"email": self.usuario.email, "password": "incorrecta"},
                format="json",
                HTTP_X_CSRFTOKEN=token,
            )
            self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        bloqueado = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"email": self.usuario.email, "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(bloqueado.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_registro_y_logout_exigen_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        for ruta, datos in [
            (reverse("cuentas:iniciar-sesion"), {"email": self.usuario.email, "password": "clave-segura"}),
            (reverse("cuentas:registro"), {
                "nombre": "Sin CSRF",
                "email": "sin-csrf@example.com",
                "password": "ClaveSegura2026!",
                "passwordConfirmacion": "ClaveSegura2026!",
            }),
        ]:
            self.assertEqual(cliente.post(ruta, datos, format="json").status_code, 403)

    def test_cierre_de_sesion(self):
        cliente, token = self.cliente_con_csrf()
        acceso = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"email": self.usuario.email, "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        salida = cliente.post(
            reverse("cuentas:cerrar-sesion"),
            format="json",
            HTTP_X_CSRFTOKEN=acceso.data["csrfToken"],
        )
        self.assertEqual(salida.status_code, status.HTTP_200_OK)
        self.assertFalse(cliente.get(reverse("cuentas:consultar-sesion")).data["autenticado"])

    def test_fusiona_carrito_local_con_carrito_de_la_cuenta(self):
        categoria = Categoria.objects.create(nombre="Pruebas")
        producto = Producto.objects.create(
            categoria=categoria,
            nombre="Producto",
            precio=Decimal("10000.00"),
            existencias=5,
        )
        ItemCarrito.objects.create(usuario=self.usuario, producto=producto, cantidad=2)
        cliente, token = self.cliente_con_csrf()
        acceso = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"email": self.usuario.email, "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        respuesta = cliente.put(
            reverse("cuentas:carrito"),
            {"items": [{"id": producto.id, "cantidad": 4}], "fusionar": True},
            format="json",
            HTTP_X_CSRFTOKEN=acceso.data["csrfToken"],
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data[0]["cantidad"], 5)

    def test_openapi_incluye_autenticacion_y_carrito(self):
        respuesta = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        rutas = respuesta.json()["paths"]
        for ruta in [
            "/api/auth/registro/",
            "/api/auth/login/",
            "/api/auth/logout/",
            "/api/auth/me/",
            "/api/auth/carrito/",
        ]:
            self.assertIn(ruta, rutas)
