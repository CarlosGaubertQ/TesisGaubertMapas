
from django.shortcuts import render
import requests
from mapas.forms import DescargaImagenForm
from .models import ImagenSatelital, Satelite, Tipo_Imagen, SubImagenSatelital
import json
import ee
from django.core.files.base import ContentFile
import geopandas as gpd

import numpy as np  # Importa la biblioteca NumPy bajo el alias 'np' para realizar cálculos numéricos.
from shapely.geometry import MultiPolygon, Polygon, LineString
from shapely.ops import split
# Create your views here.
def maps(request):
  
  if request.method == 'POST':

    if request.POST.get('guardar') == '1':
    
      #guardar imagen en la base de datos
     
      response = requests.get(request.POST.get('url'))

      if response.status_code == 200:
          satelite = Satelite.objects.get(pk=request.POST.get('satelite'))
          
          imagen_bytes = response.content
          
          tipo_imagen = Tipo_Imagen.objects.get(pk=request.POST.get('tipoImagen'))
          fecha_inicio = request.POST.get('fecha_inicio')
          fecha_fin = request.POST.get('fecha_fin')

          imagen = ImagenSatelital.objects.create(
              name=satelite.name + "_" + fecha_inicio + "_" + fecha_fin,
              coordenadas=request.POST.get('geometria'),
              satelite=satelite,
              tipo_imagen=tipo_imagen,
          )
          nombre_imagen = satelite.name + "_" + fecha_inicio + "_" + fecha_fin +".jpg"
          imagen.imagen.save( nombre_imagen, ContentFile(imagen_bytes), save=True)

          imagen.save()
          
            
          geo_path = crear_archivo_shapefile(json.loads(request.POST.get('geometria')), satelite.name, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'))
          divisionPoligonos(geo_path, satelite, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'), tipo_imagen, imagen.pk,request)
      else:
        form = DescargaImagenForm()
        return render(
          request, 
          'maps.html',
          {'form': form}
        )
      

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
  
  #print(url)
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
  
  #print("URL de la imagen en formato JPG:", url)
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
  
  #print(url)
  
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
    # Convierte la lista de listas en una lista de tuplas

    #print(geometry)
    polygon = Polygon(tuple(geometry))

    # Crea un GeoDataFrame con la geometría
    gdf = gpd.GeoDataFrame({'geometry': [polygon]})

    # Define la ruta donde deseas guardar el archivo shapefile
    ruta_guardar = 'shapefiles/nombre_shapefile.shp'

    # Guarda el GeoDataFrame como un archivo shapefile
    gdf.to_file(ruta_guardar)

    #print(f'Shapefile guardado en: {ruta_guardar}')
    return ruta_guardar

def divisionPoligonos(geo_path, satelite, fecha_inIcio, fecha_fin, tipo_imagen, pk_imagen, request):
    

    # Lee el archivo Shapefile especificado en 'geo_filepath' y lo carga en un GeoDataFrame (GeoDF).
    GeoDF = gpd.read_file(geo_path)

    # Selecciona una geometría aleatoria del GeoDataFrame 'GeoDF' y almacénala en la variable 'G'.
    G = np.random.choice(GeoDF.geometry.values)

    # Calcula la envolvente (rectángulo delimitador) de la geometría almacenada en 'G' y almacena el resultado en 'Rectangle'.
    Rectangle = G.envelope

    # Longitud del lado de la celda
    side_length = 0.02

    # Obtiene las coordenadas de la envolvente del rectángulo y las almacena en 'rect_coords'
    rect_coords = np.array(Rectangle.boundary.coords.xy)

    # Extrae las listas de coordenadas x e y de 'rect_coords'
    y_list = rect_coords[1]
    x_list = rect_coords[0]

    # Calcula los valores mínimos y máximos de las coordenadas y para obtener la altura del rectángulo
    y1 = min(y_list)
    y2 = max(y_list)

    # Calcula los valores mínimos y máximos de las coordenadas x para obtener el ancho del rectángulo
    x1 = min(x_list)
    x2 = max(x_list)

    # Calcula el ancho y la altura del rectángulo
    width = x2 - x1
    height = y2 - y1

    # Calcula el número de celdas en la dirección x e y, redondeando al entero más cercano
    xcells = int(np.round(width / side_length))
    ycells = int(np.round(height / side_length))

    # Crea una serie de índices igualmente espaciados en las direcciones x e y
    yindices = np.linspace(y1, y2, ycells + 1)
    xindices = np.linspace(x1, x2, xcells + 1)

    # Crea una lista de líneas horizontales que atraviesan el rectángulo delimitador en direcciones verticales.
    horizontal_splitters = [
        LineString([(x, yindices[0]), (x, yindices[-1])]) for x in xindices
    ]

    # Crea una lista de líneas verticales que atraviesan el rectángulo delimitador en direcciones horizontales.
    vertical_splitters = [
        LineString([(xindices[0], y), (xindices[-1], y)]) for y in yindices
    ]

    # Asigna la geometría del rectángulo delimitador original a la variable 'result'.
    result = Rectangle

    # Itera sobre la lista de líneas verticales 'vertical_splitters' y divide la geometría 'result' en múltiples polígonos.
    for splitter in vertical_splitters:
        result = MultiPolygon(split(result, splitter))

    # Itera sobre la lista de líneas horizontales 'horizontal_splitters' y divide la geometría 'result' en múltiples polígonos.
    for splitter in horizontal_splitters:
        result = MultiPolygon(split(result, splitter))

    # Extrae los polígonos individuales del resultado final 'result' y los almacena en la lista 'square_polygons'.
    square_polygons = list(result.geoms)
    

    # Crea un GeoDataFrame a partir de la lista de polígonos 'square_polygons'.
    df = gpd.GeoDataFrame(square_polygons)

    # Crea un nuevo GeoDataFrame a partir de la lista de polígonos 'square_polygons'.
    SquareGeoDF  = gpd.GeoDataFrame(square_polygons).rename(columns={0: "geometry"})

    # Crea un nuevo GeoDataFrame a partir de la lista de polígonos 'square_polygons'.
    SquareGeoDF = gpd.GeoDataFrame(square_polygons)

    # Establece la geometría del GeoDataFrame en la primera columna (índice 0) de los datos.
    SquareGeoDF = SquareGeoDF.set_geometry(0)


    # Extrae las geometrías de 'SquareGeoDF' que se intersectan con la geometría 'G' y las almacena en 'Geoms'.
    Geoms = SquareGeoDF[SquareGeoDF.intersects(G)].geometry.values

    # Define una variable 'shape' con el valor "square".
    shape = "square"

    # Define una variable 'thresh' con el valor 0.9.
    thresh = 0.2

    # Si la variable 'shape' es igual a "rhombus", realiza las siguientes operaciones.
    if shape == "rhombus":
        # Aplica una función 'rhombus(g)' a cada geometría en 'Geoms' y almacena los resultados en 'Geoms'.
        #Geoms = [rhombus(g) for g in Geoms]
        # Filtra las geometrías en 'Geoms' que cumplen con una condición de área y las almacena en 'geoms'.
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]
    # Si la variable 'shape' es igual a "square", realiza las siguientes operaciones.
    elif shape == "square":
        # Filtra las geometrías en 'Geoms' que cumplen con una condición de área y las almacena en 'geoms'.
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]


    #obtener la sub imagen y guardarla en bd
    index = 1
    for sq in geoms:
      xx, yy = sq.exterior.coords.xy
      x = xx.tolist()
      y = yy.tolist()
      url = descargar_imagen_landsat8(list(zip(x,y)), fecha_inIcio, fecha_fin, tipo_imagen)
      print(f"Imagen {index}: {url}")
      response = requests.get(url)
      if response.status_code == 200:
        #guardar sub imagen
        imagen_bytes = response.content
        imagen = ImagenSatelital.objects.get(pk=pk_imagen)
        subImagen = SubImagenSatelital.objects.create(   
            imagen=imagen
        )
        nombre_imagen = "Sub_" +satelite.name + "_" + fecha_inIcio + "_" + fecha_fin + "_"+ str(index) +".jpg"
        subImagen.subImagen.save( nombre_imagen, ContentFile(imagen_bytes), save=True)
        #geoms.loc[index-1, 'image'] = subImagen.SubImagen [[[[ REVISAR ESTO ]]]]
      else:
        form = DescargaImagenForm()
        return render(
          request, 
          'maps.html',
          {'form': form}
        )
      index += 1
    
    #print(geoms)
    grid = gpd.GeoDataFrame({'geometry':geoms})
