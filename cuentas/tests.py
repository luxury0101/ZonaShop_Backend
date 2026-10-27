from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from catalogo.models import Categoria, Producto, TallaProducto

from .models import ItemCarrito, Pedido, PerfilUsuario


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

    def datos_envio(self):
        return {
            "destinatario": "Cliente ZonaShop",
            "telefono": "3001234567",
            "direccion": "Calle 10 # 20-30",
            "ciudad": "Bogotá",
            "departamento": "Cundinamarca",
            "codigo_postal": "110111",
            "instrucciones": "Portería",
        }

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
            "/api/auth/pedidos/",
        ]:
            self.assertIn(ruta, rutas)

    def test_pago_recalcula_total_descuenta_stock_y_vacia_carrito(self):
        categoria = Categoria.objects.create(nombre="Pago")
        producto = Producto.objects.create(
            categoria=categoria,
            nombre="Chaqueta",
            precio=Decimal("75000.00"),
            existencias=4,
        )
        ItemCarrito.objects.create(
            usuario=self.usuario,
            producto=producto,
            cantidad=2,
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("cuentas:pedidos"),
            {
                "items": [
                    {"id": producto.id, "cantidad": 2},
                ],
                "envio": self.datos_envio(),
                "guardarDireccion": True,
                "total": "1.00",
                "numeroTarjeta": "4111111111111111",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(respuesta.data["total"]), Decimal("150000.00"))
        self.assertEqual(respuesta.data["estado"], Pedido.Estado.PAGADO)
        producto.refresh_from_db()
        self.assertEqual(producto.existencias, 2)
        self.assertFalse(ItemCarrito.objects.filter(usuario=self.usuario).exists())
        pedido = Pedido.objects.get(usuario=self.usuario)
        self.assertEqual(pedido.items.get().precio_unitario, Decimal("75000.00"))
        self.assertEqual(pedido.direccion_envio, "Calle 10 # 20-30")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.perfil_zonashop.ciudad, "Bogotá")

    def test_pago_sin_stock_es_atomico_y_no_crea_pedido(self):
        categoria = Categoria.objects.create(nombre="Sin stock")
        producto = Producto.objects.create(
            categoria=categoria,
            nombre="Tenis",
            precio=Decimal("120000.00"),
            existencias=1,
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("cuentas:pedidos"),
            {
                "items": [{"id": producto.id, "cantidad": 2}],
                "envio": self.datos_envio(),
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Tenis", respuesta.data["detail"])
        producto.refresh_from_db()
        self.assertEqual(producto.existencias, 1)
        self.assertFalse(Pedido.objects.exists())

    def test_historial_de_pedidos_pertenece_al_usuario(self):
        Pedido.objects.create(
            usuario=self.usuario,
            total=Decimal("40000.00"),
        )
        Pedido.objects.create(
            usuario=self.administrador,
            total=Decimal("90000.00"),
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("cuentas:pedidos"))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(Decimal(respuesta.data[0]["total"]), Decimal("40000.00"))

    def test_compra_requiere_sesion_y_csrf(self):
        ruta = reverse("cuentas:pedidos")
        datos = {
            "items": [{"id": 999, "cantidad": 1}],
            "envio": self.datos_envio(),
        }
        anonimo = APIClient(enforce_csrf_checks=True)
        self.assertIn(
            anonimo.post(ruta, datos, format="json").status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(
            cliente.post(ruta, datos, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_actualiza_perfil_direccion_y_password_manteniendo_sesion(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.patch(
            reverse("cuentas:perfil"),
            {
                "nombre": "Cliente Actualizado",
                "email": "nuevo@zonashop.test",
                "telefono": "3101234567",
                "direccion": "Carrera 7 # 10-20",
                "ciudad": "Medellín",
                "departamento": "Antioquia",
                "codigo_postal": "050001",
                "instrucciones_envio": "Apartamento 301",
                "passwordActual": "clave-segura",
                "passwordNueva": "NuevaClave2026!",
                "passwordConfirmacion": "NuevaClave2026!",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "nuevo@zonashop.test")
        self.assertEqual(self.usuario.username, "nuevo@zonashop.test")
        self.assertTrue(self.usuario.check_password("NuevaClave2026!"))
        self.assertEqual(self.usuario.perfil_zonashop.ciudad, "Medellín")
        self.assertTrue(
            self.client.get(reverse("cuentas:consultar-sesion")).data["autenticado"]
        )

    def test_solo_administrador_lista_y_actualiza_pedidos(self):
        pedido = Pedido.objects.create(
            usuario=self.usuario,
            total=Decimal("40000.00"),
            **{
                "destinatario": self.datos_envio()["destinatario"],
                "telefono_envio": self.datos_envio()["telefono"],
                "direccion_envio": self.datos_envio()["direccion"],
                "ciudad_envio": self.datos_envio()["ciudad"],
                "departamento_envio": self.datos_envio()["departamento"],
            },
        )
        self.client.force_login(self.usuario)
        self.assertEqual(
            self.client.get(reverse("cuentas:pedidos-administracion")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_login(self.administrador)
        listado = self.client.get(reverse("cuentas:pedidos-administracion"))
        self.assertEqual(listado.status_code, status.HTTP_200_OK)
        self.assertEqual(listado.data[0]["cliente"]["email"], self.usuario.email)
        actualizacion = self.client.patch(
            reverse("cuentas:actualizar-estado-pedido", kwargs={"numero": pedido.numero}),
            {"estado": Pedido.Estado.ENVIADO},
            format="json",
        )
        self.assertEqual(actualizacion.status_code, status.HTTP_200_OK)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.ENVIADO)

    def test_carrito_y_pago_separan_y_validan_stock_por_talla(self):
        categoria = Categoria.objects.create(nombre="Ropa con tallas")
        producto = Producto.objects.create(
            categoria=categoria,
            nombre="Camisa oversize",
            precio=Decimal("89900.00"),
            existencias=8,
        )
        TallaProducto.objects.bulk_create([
            TallaProducto(producto=producto, talla="XS", stock=3),
            TallaProducto(producto=producto, talla="S", stock=0),
            TallaProducto(producto=producto, talla="L", stock=5),
        ])
        self.client.force_login(self.usuario)

        carrito = self.client.put(
            reverse("cuentas:carrito"),
            {
                "items": [
                    {"id": producto.id, "cantidad": 2, "talla": "XS"},
                    {"id": producto.id, "cantidad": 4, "talla": "L"},
                ],
                "fusionar": False,
            },
            format="json",
        )
        self.assertEqual(carrito.status_code, status.HTTP_200_OK)
        self.assertEqual({item["talla"] for item in carrito.data}, {"XS", "L"})

        compra = self.client.post(
            reverse("cuentas:pedidos"),
            {
                "items": [
                    {"id": producto.id, "cantidad": 2, "talla": "XS"},
                    {"id": producto.id, "cantidad": 1, "talla": "L"},
                ],
                "envio": self.datos_envio(),
            },
            format="json",
        )
        self.assertEqual(compra.status_code, status.HTTP_201_CREATED)
        self.assertEqual({item["talla"] for item in compra.data["items"]}, {"XS", "L"})
        producto.refresh_from_db()
        self.assertEqual(producto.existencias, 5)
        self.assertEqual(producto.tallas.get(talla="XS").stock, 1)
        self.assertEqual(producto.tallas.get(talla="L").stock, 4)

    def test_pago_exige_talla_para_producto_con_tallas(self):
        categoria = Categoria.objects.create(nombre="Talla obligatoria")
        producto = Producto.objects.create(
            categoria=categoria,
            nombre="Jean",
            precio=Decimal("110000.00"),
            existencias=2,
        )
        TallaProducto.objects.create(producto=producto, talla="M", stock=2)
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse("cuentas:pedidos"),
            {
                "items": [{"id": producto.id, "cantidad": 1}],
                "envio": self.datos_envio(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Elige una talla", respuesta.data["detail"])
