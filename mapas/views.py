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


    satelite = Satelite.objects.get(id=request.POST.get('satelite'))
    tipoImagen = Tipo_Imagen.objects.get(id=request.POST.get('tipoImagen'))
    fecha_inicio = request.POST.get('fecha_inicio')
    fecha_fin = request.POST.get('fecha_fin')
    

    if satelite.name == 'Landsat8':
      descargar_imagen_landsat(geometry, fecha_inicio, fecha_fin)
    elif satelite.name == 'Sentinel-2':
      descargar_imagen_sentinel(geometry, fecha_inicio, fecha_fin)
    else:
      print("no existe este satelite")
   

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

def descargar_imagen_landsat(geometry, fecha_inicio, fecha_fin):
  # Filtrar la colección de imágenes Landsat 8
  IMGLandsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_RT_TOA') \
      .filterDate(fecha_inicio, fecha_fin) \
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


def descargar_imagen_sentinel(geometry, fecha_inicio, fecha_fin):
  # Load Sentinel-2 TOA reflectance data
  dataset = ee.ImageCollection('COPERNICUS/S2') \
      .filterDate(fecha_inicio, fecha_fin) \
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
      .filterBounds(geometry) \
      .median()



  datasetClip = dataset.clip(geometry)
  imagenRGB = datasetClip.visualize(**{'min': 0,'max': 2500, 'bands': ['B4', 'B3', 'B2']})
  extension = 'jpg'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
  print(url)