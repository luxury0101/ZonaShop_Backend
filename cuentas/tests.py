from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class AutenticacionApiTests(APITestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_user(
            username="admin",
            password="clave-segura",
            is_staff=True,
        )
        self.usuario = get_user_model().objects.create_user(
            username="visitante",
            password="clave-segura",
        )

    def cliente_con_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        respuesta = cliente.get(reverse("cuentas:obtener-csrf"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return cliente, respuesta.data["csrfToken"]

    def test_consulta_de_sesion_anonima(self):
        respuesta = self.client.get(reverse("cuentas:consultar-sesion"))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.data["autenticado"])
        self.assertIsNone(respuesta.data["usuario"])

    def test_credenciales_incorrectas_no_inician_sesion(self):
        cliente, token = self.cliente_con_csrf()

        respuesta = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"username": "admin", "password": "incorrecta"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sin_rol_administrativo_no_inicia_sesion(self):
        cliente, token = self.cliente_con_csrf()

        respuesta = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"username": "visitante", "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_inicia_y_cierra_sesion(self):
        cliente, token = self.cliente_con_csrf()

        login = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"username": "admin", "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertTrue(login.data["usuario"]["isStaff"])

        sesion = cliente.get(reverse("cuentas:consultar-sesion"))
        self.assertTrue(sesion.data["autenticado"])

        logout = cliente.post(
            reverse("cuentas:cerrar-sesion"),
            format="json",
            HTTP_X_CSRFTOKEN=login.data["csrfToken"],
        )

        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        sesion_final = cliente.get(reverse("cuentas:consultar-sesion"))
        self.assertFalse(sesion_final.data["autenticado"])

    def test_login_sin_csrf_es_rechazado(self):
        cliente = APIClient(enforce_csrf_checks=True)

        respuesta = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"username": "admin", "password": "clave-segura"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
