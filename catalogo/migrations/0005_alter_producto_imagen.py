from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0004_producto_creado_en"),
    ]

    operations = [
        migrations.AlterField(
            model_name="producto",
            name="imagen",
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to="productos/",
            ),
        ),
    ]
