from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Categoria, Producto, TallaProducto
from cuentas.models import PerfilUsuario


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

    def test_catalogo_permite_ordenar_por_precio(self):
        Producto.objects.create(
            categoria=self.categoria,
            nombre="Producto económico",
            precio=Decimal("10000.00"),
            existencias=2,
        )
        ascendente = self.client.get(reverse("producto-list"), {"orden": "precio"})
        descendente = self.client.get(reverse("producto-list"), {"orden": "-precio"})
        self.assertEqual(ascendente.data[0]["nombre"], "Producto económico")
        self.assertEqual(descendente.data[0]["nombre"], "Camiseta negra")

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

    def test_rol_administrador_protege_las_modificaciones(self):
        PerfilUsuario.objects.update_or_create(
            usuario=self.usuario,
            defaults={"rol": PerfilUsuario.Rol.ADMINISTRADOR},
        )
        self.client.force_authenticate(self.usuario)
        respuesta = self.client.patch(
            reverse("producto-detail", args=[self.producto.id]),
            {"existencias": 10},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

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

    def test_modificacion_con_sesion_requiere_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        csrf = cliente.get(reverse("cuentas:obtener-csrf"))
        login = cliente.post(
            reverse("cuentas:iniciar-sesion"),
            {"username": "admin", "password": "clave-segura"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf.data["csrfToken"],
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        sin_csrf = cliente.patch(
            reverse("producto-detail", args=[self.producto.id]),
            {"precio": "70000.00"},
            format="json",
        )
        self.assertEqual(sin_csrf.status_code, status.HTTP_403_FORBIDDEN)

        con_csrf = cliente.patch(
            reverse("producto-detail", args=[self.producto.id]),
            {"precio": "70000.00"},
            format="json",
            HTTP_X_CSRFTOKEN=login.data["csrfToken"],
        )
        self.assertEqual(con_csrf.status_code, status.HTTP_200_OK)

    def test_contenido_html_se_conserva_como_texto(self):
        self.client.force_authenticate(self.administrador)
        contenido = '<img src=x onerror="alert(1)">'

        respuesta = self.client.post(
            reverse("categoria-list"),
            {
                "nombre": "Contenido seguro",
                "descripcion": contenido,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["descripcion"], contenido)

    def test_producto_guarda_stock_por_talla_y_filtra_disponibles(self):
        self.client.force_authenticate(self.administrador)
        tallas = [
            {"talla": "XS", "stock": 3},
            {"talla": "S", "stock": 0},
            {"talla": "M", "stock": 2},
            {"talla": "L", "stock": 1},
            {"talla": "XL", "stock": 0},
        ]
        creacion = self.client.post(
            reverse("producto-list"),
            {
                "categoria": self.categoria.id,
                "nombre": "Camisa con tallas",
                "precio": "89900.00",
                "existencias": 0,
                "tallas": tallas,
            },
            format="json",
        )
        self.assertEqual(creacion.status_code, status.HTTP_201_CREATED)
        self.assertEqual(creacion.data["existencias"], 6)
        self.assertEqual(len(creacion.data["tallas"]), 5)
        self.assertTrue(creacion.data["tallas"][1]["agotada"])

        disponibles = self.client.get(reverse("producto-list"), {"talla": "M"})
        agotadas = self.client.get(reverse("producto-list"), {"talla": "XL"})
        self.assertEqual([item["nombre"] for item in disponibles.data], ["Camisa con tallas"])
        self.assertEqual(len(agotadas.data), 0)

    def test_producto_con_tallas_deriva_existencias_sin_campo_redundante(self):
        self.client.force_authenticate(self.administrador)
        respuesta = self.client.post(
            reverse("producto-list"),
            {
                "categoria": self.categoria.id,
                "nombre": "Pantalón por tallas",
                "precio": "129900.00",
                "tallas": [
                    {"talla": "S", "stock": 2},
                    {"talla": "M", "stock": 3},
                ],
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["existencias"], 5)

    def test_producto_rechaza_total_de_tallas_fuera_de_rango(self):
        self.client.force_authenticate(self.administrador)
        respuesta = self.client.post(
            reverse("producto-list"),
            {
                "categoria": self.categoria.id,
                "nombre": "Stock fuera de rango",
                "precio": "50000.00",
                "tallas": [
                    {"talla": "S", "stock": 2147483647},
                    {"talla": "M", "stock": 1},
                ],
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Producto.objects.filter(nombre="Stock fuera de rango").exists())

    def test_producto_rechaza_tallas_repetidas_o_no_permitidas(self):
        self.client.force_authenticate(self.administrador)
        for tallas in [
            [{"talla": "M", "stock": 2}, {"talla": "M", "stock": 1}],
            [{"talla": "XXL", "stock": 1}],
            [{"talla": "S", "stock": -1}],
            [{"talla": "S", "stock": 1.5}],
        ]:
            with self.subTest(tallas=tallas):
                respuesta = self.client.post(
                    reverse("producto-list"),
                    {
                        "categoria": self.categoria.id,
                        "nombre": "Producto inválido",
                        "precio": "50000.00",
                        "existencias": 0,
                        "tallas": tallas,
                    },
                    format="json",
                )
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_producto_acepta_tallas_desde_formulario_multipart(self):
        self.client.force_authenticate(self.administrador)
        respuesta = self.client.post(
            reverse("producto-list"),
            {
                "categoria": self.categoria.id,
                "nombre": "Producto desde panel",
                "precio": "70000.00",
                "existencias": "0",
                "tallas": (
                    '[{"talla":"XS","stock":2},'
                    '{"talla":"S","stock":1},'
                    '{"talla":"M","stock":0},'
                    '{"talla":"L","stock":3},'
                    '{"talla":"XL","stock":0}]'
                ),
            },
            format="multipart",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["existencias"], 6)
        self.assertEqual(len(respuesta.data["tallas"]), 5)
