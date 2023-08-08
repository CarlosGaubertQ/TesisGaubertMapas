from django.shortcuts import render

from mapas.forms import DescargaImagenForm

from .models import Satelite, Tipo_Imagen
import ee
import requests

# Create your views here.
def maps(request):
  if request.method == 'POST':
    print(request.POST)

    # Inicializar Earth Engine
  

    # Inicializa la API de Earth Engine
    ee.Initialize()

    # Define las coordenadas de un lugar boscoso o con incendios
    lat = 37.7749
    lon = -122.4194

    # Crea un punto de geometría en base a las coordenadas
    point = ee.Geometry.Point(lon, lat)

    # Define la escala en metros
    scale = 30

    # Carga la colección de imágenes satelitales Landsat
    collection = ee.ImageCollection('LANDSAT/LC08/C01/T1')

    # Filtra la colección por ubicación y fecha
    filtered_collection = collection.filterBounds(point).filterDate('2021-01-01', '2021-12-31')

    # Selecciona las bandas deseadas
    selected_bands = ['B4', 'B3', 'B2']
    filtered_collection = filtered_collection.select(selected_bands)

    # Obtiene la imagen más reciente de la colección filtrada
    image = filtered_collection.sort('system:time_start', False).first()

    # Obtiene la URL de la imagen
    image_url = image.getThumbURL({'region': point, 'scale': scale})

    # Imprime la URL de la imagen
    print('URL de la imagen:', image_url)
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