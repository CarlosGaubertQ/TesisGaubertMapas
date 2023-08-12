from django.shortcuts import render

from mapas.forms import DescargaImagenForm

from .models import Satelite, Tipo_Imagen

import geemap as gm
import ee

# Create your views here.
def maps(request):
  if request.method == 'POST':

    # Inicializar la API de Google Earth Engine
    ee.Initialize()

    # Definir la geometría
    geometry = ee.Geometry.Polygon(
        [[[-73.13409353690751, -36.70853462255544],
          [-73.13409353690751, -36.833940272098495],
          [-72.75849844413408, -36.833940272098495],
          [-72.75849844413408, -36.70853462255544]]])

    # Filtrar la colección de imágenes Landsat 8
    IMGLandsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_RT_TOA') \
        .filterDate('2018-04-01', '2018-12-30') \
        .filterBounds(geometry) \
        .filterMetadata('CLOUD_COVER', 'less_than', 20)

    # Obtener la imagen mediana
    Landsat8Filtro = IMGLandsat8.median()

    # Recortar la imagen con la geometría
    Landsat8Clip = Landsat8Filtro.clip(geometry)

    # Descargar la imagen
    url = Landsat8Clip.select("B4", "B3", "B2").getDownloadURL({
        'name': 'Landsat8_30m',
        'scale': 30,
        'region': geometry
    })

    # Descargar el archivo
    import urllib.request
    urllib.request.urlretrieve(url, 'Landsat8_30m.tif')

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

 
def get_image_url(latitude, longitude):
    # Crear un punto a partir de la latitud y longitud
    point = ee.Geometry.Point(longitude, latitude)

    # Obtener la colección de imágenes satelitales Landsat
    collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
        .filterBounds(point) \
        .filter(ee.Filter.lt('CLOUD_COVER', 10)) \
        .sort('CLOUD_COVER') \
        .limit(1)

    # Obtener la imagen con la menor cantidad de nubes
    image = ee.Image(collection.first())

    # Seleccionar las bandas para la codificación en formato PNG
    bands = ['B4', 'B3', 'B2']  # Bandas roja, verde, azul

    # Obtener la URL de la imagen
    url = image.getThumbURL({
        'bands': bands,
        'scale': 30,  # Escala espacial en metros
        'region': point
    })

    return url