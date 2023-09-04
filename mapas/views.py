
from django.shortcuts import render
import requests
from mapas.forms import DescargaImagenForm
from .models import ImagenSatelital, Satelite, Tipo_Imagen
import json
import ee
from django.core.files.base import ContentFile

# Create your views here.
def maps(request):
  
  if request.method == 'POST':
    print(request.POST)
    if request.POST.get('guardar') == '1':
      print("guardar imagen")
      #guardar imagen en la base de datos
      print(request.POST)
      response = requests.get(request.POST.get('url'))

      if response.status_code == 200:
          imagen_bytes = response.content
          satelite = Satelite.objects.get(pk=request.POST.get('satelite'))
          tipo_imagen = Tipo_Imagen.objects.get(pk=request.POST.get('tipoImagen'))

          imagen = ImagenSatelital.objects.create(
              name="Título de la imagen",
              coordenadas=request.POST.get('geometria'),
              satelite=satelite,
              tipo_imagen=tipo_imagen,
          )
          imagen.imagen.save("nombre_de_archivo.jpg", ContentFile(imagen_bytes), save=True)

          imagen.save()

      else:
        form = DescargaImagenForm()
        return render(
          request, 
          'maps.html',
          {'form': form}
        )

      #GUARDAR SHAPEFILE
      satelite = Satelite.objects.get(id=request.POST.get('satelite'))
      print(satelite.name)
      
      crear_archivo_shapefile(request.POST.get('geometria'), satelite.name, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'))

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
      porcentaje= 0
      
      if satelite.name == 'Landsat8':
        url = descargar_imagen_landsat8(json.loads(request.POST.get('geometria')), fecha_inicio, fecha_fin, tipoImagen)
        porcentaje = calcular_porcentaje_bosque(json.loads(request.POST.get('geometria')), fecha_inicio, fecha_fin)
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
        'metros_cuadrados': request.POST.get('metros_cuadrados'),
        'porcentaje': porcentaje
        }
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
  elif tipoImagen.name == 'Agriculture':
    band = ['B6', 'B5', 'B2']
  elif tipoImagen.name == 'Urban':
    band = ['B7', 'B6', 'B4']
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
  elif tipoImagen.name == 'Agriculture':
    band = ['B5', 'B4', 'B3']
  elif tipoImagen.name == 'Urban':
    band = ['B7', 'B5', 'B3']
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
  elif tipoImagen.name == 'Agriculture':
    band = ['B11', 'B8', 'B2']
  elif tipoImagen.name == 'Urban':
    band = ['B12', 'B11', 'B4']
  
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
   
def calcular_porcentaje_bosque(geometry, fecha_inicio, fecha_fin):
    # Inicializar la API de Google Earth Engine
    ee.Initialize()

    geometry = ee.Geometry.Polygon(
    geometry);

    # Filtrar la colección Landsat 8
    landsat_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_RT_TOA') \
        .filterDate(fecha_inicio, fecha_fin) \
        .filterBounds(geometry) \
        .filterMetadata('CLOUD_COVER', 'less_than', 20)

    # Obtener la imagen mediana de la colección
    landsat_median = landsat_collection.median()

    # Calcular el NDVI (Índice de Vegetación de Diferencia Normalizada)
    ndvi = landsat_median.normalizedDifference(['B5', 'B4'])

    # Aplicar umbral para identificar bosques (ajusta el umbral según tu necesidad)
    threshold = 0.2
    bosque = ndvi.gt(threshold)

    # Calcular el porcentaje de bosque en la región de interés
    area_bosque = bosque.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=30  # Resolución espacial de Landsat
    )

    total_area = geometry.area()
    porcentaje_bosque = area_bosque.getInfo()['nd'] / total_area.getInfo()
    resultado = round(porcentaje_bosque * 100, 2)
    return "{:.2f}".format(resultado)

def crear_archivo_shapefile(geometry, satelite, fecha_inicio, fecha_fin):
  ee.Initialize()
  geometry = ee.Geometry.Polygon(
    [geometry], None, False);
  # Exporta la geometría a un shapefile
  task = ee.batch.Export.table.toDrive(
      collection=ee.FeatureCollection(geometry),
      description= satelite + '_' + fecha_inicio + '_' + fecha_fin,
      folder='TesisGaubert/' + satelite + '/',
      fileFormat='SHP')

  # Inicia la tarea de exportación
  task.start()