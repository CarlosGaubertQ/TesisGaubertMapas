from django.db import models

# Create your models here.
class Satelite(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self) :
        return self.name

class Tipo_Imagen(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self) :
        return self.name
    
class ImagenSatelital(models.Model):
    name = models.CharField(max_length=255)
    coordenadas = models.TextField()
    imagen = models.ImageField(upload_to='imagenes/')
    satelite = models.ForeignKey(Satelite, on_delete=models.CASCADE)
    tipo_imagen = models.ForeignKey(Tipo_Imagen, on_delete=models.CASCADE)

    def __str__(self):
        return self.name