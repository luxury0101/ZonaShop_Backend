from io import BytesIO
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageOps

from catalogo.models import Categoria, Producto, TallaProducto


CATEGORIAS = {
    "Camisetas": "Camisas y camisetas esenciales para combinar en cualquier temporada.",
    "Jeans": "Pantalones, denim y siluetas urbanas para el día a día.",
    "Chaquetas y buzos": "Capas ligeras y abrigadas con acabados contemporáneos.",
    "Vestidos y faldas": "Prendas fluidas y estructuradas para distintos momentos.",
    "Calzado": "Calzado versátil de líneas limpias y materiales resistentes.",
    "Accesorios": "Complementos funcionales para terminar cada look.",
}


PRODUCTOS = [
    {
        "categoria": "Camisetas",
        "nombre": "Camisa Lino Bruma",
        "descripcion": "Camisa de mezcla de lino y algodón con textura ligera. Su corte relajado funciona en looks formales o casuales.",
        "precio": "129900",
        "tallas": {"S": 5, "M": 7, "L": 6, "XL": 4},
    },
    {
        "categoria": "Camisetas",
        "nombre": "Camiseta Rib Horizonte",
        "descripcion": "Camiseta en algodón acanalado de tacto suave. Tiene silueta recta y cuello reforzado.",
        "precio": "69900",
        "tallas": {"S": 8, "M": 10, "L": 7, "XL": 5},
    },
    {
        "categoria": "Camisetas",
        "nombre": "Camisa Oxford Noche",
        "descripcion": "Camisa de algodón Oxford con acabado mate y botones tono a tono. Una pieza limpia para capas y estilismos monocromáticos.",
        "precio": "159900",
        "tallas": {"S": 3, "M": 6, "L": 5, "XL": 2},
    },
    {
        "categoria": "Camisetas",
        "nombre": "Camiseta Box Arena",
        "descripcion": "Camiseta de algodón pesado con corte cuadrado y hombro caído. Conserva la forma y ofrece una caída estructurada.",
        "precio": "89900",
        "tallas": {"S": 4, "M": 8, "L": 6, "XL": 3},
    },
    {
        "categoria": "Jeans",
        "nombre": "Pantalón Sastre Grafito",
        "descripcion": "Pantalón de sarga con pinzas frontales y caída amplia. El acabado grafito aporta una apariencia sobria y versátil.",
        "precio": "169900",
        "tallas": {"S": 3, "M": 5, "L": 4, "XL": 2},
    },
    {
        "categoria": "Jeans",
        "nombre": "Jean Recto Ceniza",
        "descripcion": "Jean de denim rígido con lavado ceniza y pierna recta. Diseñado para uso diario y combinaciones neutras.",
        "precio": "139900",
        "tallas": {"S": 4, "M": 7, "L": 5, "XL": 2},
    },
    {
        "categoria": "Jeans",
        "nombre": "Pantalón Cargo Umbral",
        "descripcion": "Cargo en algodón resistente con bolsillos laterales discretos. Su volumen relajado mantiene una línea urbana limpia.",
        "precio": "149900",
        "tallas": {"S": 5, "M": 6, "L": 4, "XL": 3},
    },
    {
        "categoria": "Chaquetas y buzos",
        "nombre": "Chaqueta Eclipse",
        "descripcion": "Chaqueta acolchada de nylon mate con forro liviano. Su silueta corta crea una capa contemporánea para clima frío.",
        "precio": "249900",
        "tallas": {"S": 0, "M": 0, "L": 0, "XL": 0},
    },
    {
        "categoria": "Chaquetas y buzos",
        "nombre": "Buzo Cuello Bruma",
        "descripcion": "Buzo de algodón perchado con cuello alto y puños reforzados. Ofrece abrigo suave sin perder una forma depurada.",
        "precio": "119900",
        "tallas": {"S": 4, "M": 7, "L": 5, "XL": 3},
    },
    {
        "categoria": "Chaquetas y buzos",
        "nombre": "Chaqueta Denim Índigo",
        "descripcion": "Chaqueta de denim índigo con costuras contrastantes y corte regular. Una capa duradera para estilismos cotidianos.",
        "precio": "219900",
        "tallas": {"S": 3, "M": 5, "L": 4, "XL": 2},
    },
    {
        "categoria": "Vestidos y faldas",
        "nombre": "Vestido Midi Nocturno",
        "descripcion": "Vestido midi en tejido fluido con escote limpio y caída suave. Su tono oscuro permite llevarlo de día o de noche.",
        "precio": "189900",
        "tallas": {"S": 3, "M": 5, "L": 4, "XL": 2},
    },
    {
        "categoria": "Vestidos y faldas",
        "nombre": "Falda Plisada Órbita",
        "descripcion": "Falda midi de poliéster reciclado con pliegues finos. El movimiento ligero contrasta con su acabado mate.",
        "precio": "99900",
        "tallas": {"S": 1, "M": 1, "L": 0, "XL": 0},
    },
    {
        "categoria": "Vestidos y faldas",
        "nombre": "Vestido Satén Aura",
        "descripcion": "Vestido largo en satén de brillo controlado y tirantes ajustables. La silueta fluida crea un acabado elegante y sencillo.",
        "precio": "229900",
        "tallas": {"S": 2, "M": 4, "L": 3, "XL": 1},
    },
    {
        "categoria": "Calzado",
        "nombre": "Tenis Urbanos Lumen",
        "descripcion": "Tenis de lona gruesa con suela de caucho flexible. Su diseño limpio acompaña prendas casuales y sastrería relajada.",
        "precio": "199900",
        "existencias": 12,
    },
    {
        "categoria": "Calzado",
        "nombre": "Botín Chelsea Sombra",
        "descripcion": "Botín en cuero sintético texturizado con laterales elásticos. La suela robusta aporta estabilidad y una presencia sobria.",
        "precio": "299900",
        "existencias": 7,
    },
    {
        "categoria": "Calzado",
        "nombre": "Mocasín Esencial Marfil",
        "descripcion": "Mocasín de acabado mate con plantilla acolchada y costura tonal. Combina una línea clásica con comodidad diaria.",
        "precio": "239900",
        "existencias": 3,
    },
    {
        "categoria": "Accesorios",
        "nombre": "Gorra Panel Ceniza",
        "descripcion": "Gorra de algodón lavado con seis paneles y ajuste metálico. Su tono ceniza complementa paletas neutras.",
        "precio": "59900",
        "existencias": 14,
    },
    {
        "categoria": "Accesorios",
        "nombre": "Cinturón Cuero Umbral",
        "descripcion": "Cinturón de cuero sintético granulado con hebilla de metal cepillado. Tiene una anchura versátil para jeans o pantalones de vestir.",
        "precio": "79900",
        "existencias": 10,
    },
    {
        "categoria": "Accesorios",
        "nombre": "Bolso Estructurado Nébula",
        "descripcion": "Bolso de material vegano con cuerpo estructurado y correa regulable. Incluye compartimentos interiores para uso cotidiano.",
        "precio": "179900",
        "existencias": 6,
    },
    {
        "categoria": "Accesorios",
        "nombre": "Reloj Minimal Línea",
        "descripcion": "Reloj de caja metálica con esfera limpia y correa de cuero sintético. Un accesorio discreto de inspiración arquitectónica.",
        "precio": "399900",
        "existencias": 2,
    },
]


# Fotografías provisionales de producto sin modelos identificables.
# Todas pertenecen a páginas marcadas como gratuitas por Pexels.
IMAGENES = {
    "Camiseta Rib Horizonte": [
        "https://images.pexels.com/photos/581087/pexels-photo-581087.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/3927390/pexels-photo-3927390.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
    "Jean Recto Ceniza": [
        "https://images.pexels.com/photos/20777875/pexels-photo-20777875.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/33516576/pexels-photo-33516576.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
    "Vestido Midi Nocturno": [
        "https://images.pexels.com/photos/19895964/pexels-photo-19895964.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/35538618/pexels-photo-35538618.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
    "Falda Plisada Órbita": [
        "https://images.pexels.com/photos/19895965/pexels-photo-19895965.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/35538618/pexels-photo-35538618.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
    "Bolso Estructurado Nébula": [
        "https://images.pexels.com/photos/33552355/pexels-photo-33552355.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/4076565/pexels-photo-4076565.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
    "Reloj Minimal Línea": [
        "https://images.pexels.com/photos/3892369/pexels-photo-3892369.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "https://images.pexels.com/photos/4076565/pexels-photo-4076565.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ],
}


class Command(BaseCommand):
    help = "Crea o actualiza el catálogo de demostración de ZonaShop sin duplicar productos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sin-imagenes",
            action="store_true",
            help="Omite la descarga y carga de imágenes provisionales.",
        )
        parser.add_argument(
            "--enlaces-directos",
            action="store_true",
            help="Guarda las URLs de Pexels sin copiarlas al storage configurado.",
        )

    def _preparar_imagen(self, url):
        request = Request(
            url,
            headers={"User-Agent": "ZonaShop catalog seed/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            contenido = response.read(8 * 1024 * 1024)

        with Image.open(BytesIO(contenido)) as original:
            imagen = ImageOps.exif_transpose(original).convert("RGB")
            imagen = ImageOps.fit(
                imagen,
                (1000, 1250),
                method=Image.Resampling.LANCZOS,
            )
            salida = BytesIO()
            imagen.save(salida, format="WEBP", quality=82, method=6)
        return ContentFile(salida.getvalue())

    def _guardar_imagenes(self, producto, urls, enlaces_directos=False):
        campos = ("imagen", "imagen_secundaria")
        for posicion, (campo, url) in enumerate(zip(campos, urls), start=1):
            archivo_actual = getattr(producto, campo)
            if archivo_actual:
                continue
            if enlaces_directos:
                setattr(producto, campo, url)
                producto.save(update_fields=[campo])
                self.stdout.write(f"  enlace {posicion}: {producto.nombre}")
                continue
            try:
                contenido = self._preparar_imagen(url)
                nombre = f"seed/{slugify(producto.nombre)}-{posicion}.webp"
                archivo_actual.save(nombre, contenido, save=True)
                self.stdout.write(f"  imagen {posicion}: {producto.nombre}")
            except Exception as error:  # La carga de datos no debe fallar por una foto externa.
                self.stderr.write(
                    self.style.WARNING(
                        f"  imagen omitida para {producto.nombre}: {error}"
                    )
                )

    def handle(self, *args, **opciones):
        categorias = {}
        for nombre, descripcion in CATEGORIAS.items():
            categoria, creada = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion},
            )
            categorias[nombre] = categoria
            if creada:
                self.stdout.write(self.style.SUCCESS(f"Categoría creada: {nombre}"))

        productos_guardados = []
        with transaction.atomic():
            for datos in PRODUCTOS:
                tallas = datos.get("tallas")
                existencias = (
                    sum(tallas.values())
                    if tallas is not None
                    else datos["existencias"]
                )
                producto, creado = Producto.objects.update_or_create(
                    nombre=datos["nombre"],
                    defaults={
                        "categoria": categorias[datos["categoria"]],
                        "descripcion": datos["descripcion"],
                        "precio": datos["precio"],
                        "existencias": existencias,
                    },
                )
                producto.tallas.all().delete()
                if tallas is not None:
                    TallaProducto.objects.bulk_create([
                        TallaProducto(
                            producto=producto,
                            talla=talla,
                            stock=stock,
                        )
                        for talla, stock in tallas.items()
                    ])
                productos_guardados.append(producto)
                estado = "creado" if creado else "actualizado"
                self.stdout.write(f"Producto {estado}: {producto.nombre}")

        if not opciones["sin_imagenes"]:
            for producto in productos_guardados:
                urls = IMAGENES.get(producto.nombre)
                if urls:
                    self._guardar_imagenes(
                        producto,
                        urls,
                        enlaces_directos=opciones["enlaces_directos"],
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Catálogo listo: {len(productos_guardados)} productos procesados."
        ))
