from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0006_tallaproducto"),
    ]

    operations = [
        migrations.AlterField(
            model_name="categoria",
            name="descripcion",
            field=models.TextField(blank=True, default="", max_length=2000),
        ),
        migrations.AlterField(
            model_name="producto",
            name="descripcion",
            field=models.TextField(blank=True, default="", max_length=4000),
        ),
        migrations.AddField(
            model_name="producto",
            name="imagen_secundaria",
            field=models.ImageField(blank=True, max_length=500, null=True, upload_to="productos/"),
        ),
    ]
