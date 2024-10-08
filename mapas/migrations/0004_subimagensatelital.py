# Generated by Django 4.2.2 on 2023-09-13 17:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mapas', '0003_rename_imagen_imagensatelital'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubImagenSatelital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subImagen', models.ImageField(upload_to='imagenes/subimagen/')),
                ('imagen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mapas.imagensatelital')),
            ],
        ),
    ]
