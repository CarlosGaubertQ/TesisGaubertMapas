
from tkinter import Label
from django.shortcuts import render
from mapas.forms import DescargaImagenForm
from .models import Satelite, Tipo_Imagen
import json
import ee
# Create your views here.
def maps(request):
  
  if request.method == 'POST':
    print(request.POST)
    
    if request.POST.get('guardar') == '1':
      print("guardar imagen")
      #guardar imagen en la base de datos




      # REALIZAR GUARDAR IMAGEN
      form = DescargaImagenForm()
      return render(
        request, 
        'maps.html',
        {'form': form}
      )
    elif request.POST.get('guardar') == '0':
      form = DescargaImagenForm()
      return render(
        request, 
        'maps.html',
        {'form': form}
      )
    else: 

      satelite = Satelite.objects.get(id=request.POST.get('satelite'))
      tipoImagen = Tipo_Imagen.objects.get(id=request.POST.get('tipoImagen'))
      fecha_inicio = request.POST.get('fecha_inicio')
      fecha_fin = request.POST.get('fecha_fin')

      
      if satelite.name == 'Landsat8':
        url = descargar_imagen_landsat8(json.loads(request.POST.get('geometria')), fecha_inicio, fecha_fin, tipoImagen)
      elif satelite.name == 'Landsat7':
        url = descargar_imagen_landsat7(json.loads(request.POST.get('geometria')), fecha_inicio, fecha_fin, tipoImagen)
      elif satelite.name == 'Sentinel-2':
        url = descargar_imagen_sentinel(json.loads(request.POST.get('geometria')), fecha_inicio, fecha_fin, tipoImagen)
      else:
        print("no existe este satelite")

      return render(
        request, 
        'visualizar_imagen.html',
        {'url': url, 
        'geometria': request.POST.get('geometria'),
        'satelite': request.POST.get('satelite'),
        'tipoImagen': request.POST.get('tipoImagen'),
        'fecha_inicio': request.POST.get('fecha_inicio'),
        'fecha_fin': request.POST.get('fecha_fin'),
        'metros_cuadrados': request.POST.get('metros_cuadrados')}
      )
  else:
    form = DescargaImagenForm()
    return render(
        request, 
        'maps.html',
        {'form': form}
      )
  

def vista_satelite(request, url):
  return render(
        request, 
        'visualizar_imagen.html',
        {'url': url}
  )


def descargar_imagen_landsat8(geometry, fecha_inicio, fecha_fin, tipoImagen):
  band = ['B4', 'B3', 'B2']

  if tipoImagen.name == 'True color':
    band = ['B4', 'B3', 'B2']
  elif tipoImagen.name == 'False color':
    band = ['B10', 'B4', 'B3']
  # Inicializar la API de Google Earth Engine
  ee.Initialize()

  # Definir la geometría
  geometry = ee.Geometry.Polygon(
    [geometry], None, False);
  
  IMGLandsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_RT_TOA') \
      .filterDate(fecha_inicio, fecha_fin) \
      .filterBounds(geometry) \
      .filterMetadata('CLOUD_COVER', 'less_than', 20)

  # Obtener la imagen mediana
  Landsat8Filtro = IMGLandsat8.median()

  # Recortar la imagen con la geometría
  Landsat8Clip = Landsat8Filtro.clip(geometry)



  imagenRGB = Landsat8Clip.visualize(**{'min': 0,'max': 0.5, 'bands': band})
  extension = 'jpg'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
  print(url)
  return url
  
def descargar_imagen_landsat7(geometry, fecha_inicio, fecha_fin, tipoImagen):
  band = ['B3', 'B2', 'B1']

  if tipoImagen.name == 'True color':
    band = ['B3', 'B2', 'B1']
  elif tipoImagen.name == 'False color':
    band = ['B4', 'B3', 'B2']

  # Inicializar la API de Google Earth Engine
  ee.Initialize()

  # Definir la geometría
  geometry = ee.Geometry.Polygon(
    [geometry], None, False);
  
  # Filtra la colección de imágenes Landsat 7
  l7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")
        .filterDate(fecha_inicio, fecha_fin)
        .filterBounds(geometry)
        .sort('CLOUD_COVER', True)
        .first())

  # Calcula el promedio focal
  img_fill = l7.focal_mean(1, 'square', 'pixels', 8)

  # Combina la imagen promedio con la imagen Landsat 7 original
  final_image = img_fill.blend(l7)

  # Obtiene una URL para la imagen en formato JPG
  url = final_image.clip(geometry).getThumbUrl({'min': 0, 'max': 0.3, 'gamma': 1.4, 'bands': band, 'format': 'jpg'})

  print("URL de la imagen en formato JPG:", url)
  return url
  



def descargar_imagen_sentinel(geometry, fecha_inicio, fecha_fin, tipoImagen):
  
  band = ['B4', 'B3', 'B2']

  if tipoImagen.name == 'True color':
    band = ['B4', 'B3', 'B2']
  elif tipoImagen.name == 'False color':
    band = ['B8', 'B4', 'B3']

  
  # Inicializar la API de Google Earth Engine
  ee.Initialize()

  # Definir la geometría
  geometry = ee.Geometry.Polygon(
    [geometry], None, False);
  # Load Sentinel-2 TOA reflectance data
  dataset = ee.ImageCollection('COPERNICUS/S2') \
      .filterDate(fecha_inicio, fecha_fin) \
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
      .filterBounds(geometry) \
      .median()



  datasetClip = dataset.clip(geometry)
  imagenRGB = datasetClip.visualize(**{'min': 0,'max': 2500, 'bands': band})
  extension = 'jpg'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
  print(url)
  return url
   
