from django.shortcuts import render

from mapas.forms import DescargaImagenForm

from .models import Satelite, Tipo_Imagen

import ee
import json
# Create your views here.
def maps(request):
  if request.method == 'POST':
    geometria = json.loads(request.POST.get('geometria'))
    # Inicializar la API de Google Earth Engine
    ee.Initialize()

    # Definir la geometría
    geometry = ee.Geometry.Polygon(
        [geometria], None, False);

  


    # Filtrar la colección de imágenes Landsat 8
    IMGLandsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_RT_TOA') \
        .filterDate('2018-04-01', '2018-12-30') \
        .filterBounds(geometry) \
        .filterMetadata('CLOUD_COVER', 'less_than', 20)

    # Obtener la imagen mediana
    Landsat8Filtro = IMGLandsat8.median()

    # Recortar la imagen con la geometría
    Landsat8Clip = Landsat8Filtro.clip(geometry)


    imagenRGB = Landsat8Clip.visualize(**{'min': 0,'max': 0.5, 'bands': ['B4', 'B3', 'B2']})
    extension = 'jpg'

    url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
    print(url)

    form = DescargaImagenForm()
    return render(
        request, 
        'maps.html',
        {'form': form}
      )
  else:
    form = DescargaImagenForm()
    return render(
        request, 
        'maps.html',
        {'form': form}
      )

 
