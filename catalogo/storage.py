from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from vercel.blob import sync as blob


@deconstructible
class VercelBlobStorage(Storage):
    """Almacenamiento público y persistente para imágenes de productos."""

    access = "public"

    def _open(self, name, mode="rb"):
        if mode not in {"r", "rb"}:
            raise ValueError("Vercel Blob solo permite abrir archivos en lectura.")

        resultado = blob.get_blob(name, access=self.access)
        return ContentFile(resultado.body, name=name)

    def _save(self, name, content):
        content.seek(0)
        resultado = blob.put_blob(
            name,
            content,
            access=self.access,
            content_length=content.size,
            content_type=getattr(content, "content_type", None),
            add_random_suffix=True,
            cache_control_max_age=31536000,
        )
        return resultado.url

    def delete(self, name):
        if name:
            blob.delete_blob(name)

    def exists(self, name):
        # Cada carga recibe un sufijo aleatorio en Vercel Blob.
        return False

    def size(self, name):
        return blob.head_blob(name).size

    def url(self, name):
        if name.startswith("https://"):
            return name
        return blob.head_blob(name).url
