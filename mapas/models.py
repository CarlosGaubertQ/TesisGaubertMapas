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