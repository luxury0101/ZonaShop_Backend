from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Categoria, Producto


class CatalogoApiTests(APITestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre="Camisetas",
            descripcion="Ropa casual",
        )
        self.otra_categoria = Categoria.objects.create(
            nombre="Accesorios",
        )
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Camiseta negra",
            descripcion="Algodón",
            precio=Decimal("50000.00"),
            existencias=8,
        )
        self.administrador = get_user_model().objects.create_user(
            username="admin",
            password="clave-segura",
            is_staff=True,
        )
        self.usuario = get_user_model().objects.create_user(
            username="visitante",
            password="clave-segura",
        )

    def test_catalogo_es_publico_y_filtra_por_categoria(self):
        Producto.objects.create(
            categoria=self.otra_categoria,
            nombre="Gorra",
            precio=Decimal("30000.00"),
            existencias=3,
        )

        respuesta = self.client.get(
            reverse("producto-list"),
            {"categoria": self.categoria.id},
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(respuesta.data[0]["nombre"], "Camiseta negra")

    def test_usuario_anonimo_no_puede_crear_categorias(self):
        respuesta = self.client.post(
            reverse("categoria-list"),
            {"nombre": "Calzado", "descripcion": "Zapatos"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Categoria.objects.filter(nombre="Calzado").exists())

    def test_usuario_sin_permisos_no_puede_modificar_productos(self):
        self.client.force_authenticate(self.usuario)

        respuesta = self.client.patch(
            reverse("producto-detail", args=[self.producto.id]),
            {"precio": "60000.00"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.precio, Decimal("50000.00"))

    def test_administrador_puede_crear_y_editar_productos(self):
        self.client.force_authenticate(self.administrador)

        creacion = self.client.post(
            reverse("producto-list"),
            {
                "categoria": self.categoria.id,
                "nombre": "Camiseta blanca",
                "descripcion": "Algodón",
                "precio": "45000.00",
                "existencias": 5,
            },
            format="json",
        )

        self.assertEqual(creacion.status_code, status.HTTP_201_CREATED)

        edicion = self.client.patch(
            reverse("producto-detail", args=[creacion.data["id"]]),
            {"precio": "47000.00", "existencias": 4},
            format="json",
        )

        self.assertEqual(edicion.status_code, status.HTTP_200_OK)
        self.assertEqual(edicion.data["precio"], "47000.00")
        self.assertEqual(edicion.data["existencias"], 4)

    def test_api_rechaza_datos_invalidos_de_producto(self):
        self.client.force_authenticate(self.administrador)

        casos = [
            {
                "categoria": self.categoria.id,
                "nombre": "Precio inválido",
                "precio": "0.00",
                "existencias": 1,
            },
            {
                "categoria": self.categoria.id,
                "nombre": "Stock inválido",
                "precio": "10000.00",
                "existencias": -1,
            },
            {
                "categoria": 999999,
                "nombre": "Categoría inválida",
                "precio": "10000.00",
                "existencias": 1,
            },
        ]

        for datos in casos:
            with self.subTest(datos=datos):
                respuesta = self.client.post(
                    reverse("producto-list"),
                    datos,
                    format="json",
                )
                self.assertEqual(
                    respuesta.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_no_se_elimina_categoria_con_productos(self):
        self.client.force_authenticate(self.administrador)

        respuesta = self.client.delete(
            reverse("categoria-detail", args=[self.categoria.id])
        )

        self.assertEqual(respuesta.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.id).exists())

    def test_administrador_elimina_categoria_vacia(self):
        self.client.force_authenticate(self.administrador)

        respuesta = self.client.delete(
            reverse("categoria-detail", args=[self.otra_categoria.id])
        )

        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Categoria.objects.filter(pk=self.otra_categoria.id).exists()
        )
