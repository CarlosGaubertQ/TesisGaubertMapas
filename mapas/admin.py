from django.contrib import admin
from .models import Satelite, Tipo_Imagen, ImagenSatelital


# Register your models here.
admin.site.register(Satelite)
admin.site.register(Tipo_Imagen)
admin.site.register(ImagenSatelital)