from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase

from .storage import VercelBlobStorage


class VercelBlobStorageTests(SimpleTestCase):
    def setUp(self):
        self.storage = VercelBlobStorage()

    @patch("catalogo.storage.blob.put_blob")
    def test_guarda_y_conserva_la_url_publica(self, put_blob):
        put_blob.return_value = SimpleNamespace(
            url=(
                "https://tienda.public.blob.vercel-storage.com/"
                "productos/chaqueta-abc.png"
            )
        )
        contenido = ContentFile(b"imagen", name="chaqueta.png")

        nombre = self.storage._save("productos/chaqueta.png", contenido)

        self.assertEqual(nombre, put_blob.return_value.url)
        put_blob.assert_called_once_with(
            "productos/chaqueta.png",
            contenido,
            access="public",
            content_length=6,
            content_type=None,
            add_random_suffix=True,
            cache_control_max_age=31536000,
        )
        self.assertEqual(self.storage.url(nombre), nombre)

    @patch("catalogo.storage.blob.delete_blob")
    def test_elimina_el_blob_por_su_url(self, delete_blob):
        url = "https://tienda.public.blob.vercel-storage.com/producto.png"

        self.storage.delete(url)

        delete_blob.assert_called_once_with(url)
