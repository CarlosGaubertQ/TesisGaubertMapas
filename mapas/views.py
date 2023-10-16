
import base64
import io
from django.shortcuts import render
import requests
from mapas.forms import DescargaImagenForm, ImagenesDescargadasForm
from .models import ImagenSatelital, Satelite, Tipo_Imagen, SubImagenSatelital
import json
import ee
from django.core.files.base import ContentFile
import geopandas as gpd
import os
from django.conf import settings
import numpy as np  
from shapely.geometry import MultiPolygon, Polygon, LineString
from shapely.ops import split

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import shutil



def maps(request):
  
  if request.method == 'POST':

    try:

      id_imagen = request.POST.get('imagenes')

      imagen_satelital = ImagenSatelital.objects.get(pk=id_imagen)
      años = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
      decrecimiento_forestal = [100, 95, 92, 89, 85, 80, 75, 70, 65, 60, 55] 


      plt.figure(figsize=(8, 6))
      plt.plot(años, decrecimiento_forestal, marker='o', color='b', linestyle='-', linewidth=2, markersize=8)
      plt.title('Decrecimiento Forestal por Año')
      plt.xlabel('Año')
      plt.ylabel('Porcentaje de Decrecimiento')
      plt.grid(True)
      plt.xticks(años, rotation=45) 

     
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png')
      buffer.seek(0)
      plt.close()

      imagen_base64 = base64.b64encode(buffer.read()).decode()


      contexto = {
          'imagen_base64': imagen_base64,
          'imagen_satelital': imagen_satelital,
      }
      return render(
        request,
        'evaluacion.html',
        contexto
      
      )
    except Exception as e:
      print(f"ERROR : {e}")
   
      if request.POST.get('guardar') == '1':
      
        #guardar imagen en la base de datos
      
        response = requests.get(request.POST.get('url'))

        if response.status_code == 200:
            satelite = Satelite.objects.get(pk=request.POST.get('satelite'))
            
            imagen_bytes = response.content
            
            tipo_imagen = Tipo_Imagen.objects.get(pk=request.POST.get('tipoImagen'))
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            titulo = request.POST.get('titulo')
            nombre_imagen = titulo +"_" + satelite.name + "_" + fecha_inicio + "_" + fecha_fin +".png"
            imagen = ImagenSatelital.objects.create(
                name=nombre_imagen,
                coordenadas=request.POST.get('geometria'),
                satelite=satelite,
                tipo_imagen=tipo_imagen,
            )
            imagen.imagen.save( nombre_imagen, ContentFile(imagen_bytes), save=True)

            imagen.save()
            
              
            geo_path = crear_archivo_shapefile(json.loads(request.POST.get('geometria')), satelite.name, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'))
            divisionPoligonos(geo_path, satelite, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'), tipo_imagen, imagen.pk,request, titulo)
        else:
          form = DescargaImagenForm()
          form_imagenes =ImagenesDescargadasForm()
          return render(
            request, 
            'maps.html',
            {'form': form,
            'form_imagenes': form_imagenes}
          )
        

        # REALIZAR GUARDAR IMAGEN
        form = DescargaImagenForm()
        form_imagenes = ImagenesDescargadasForm()
        return render(
            request, 
            'maps.html',
            {'form': form,
            'form_imagenes': form_imagenes}
        )
      elif request.POST.get('guardar') == '0':
        form = DescargaImagenForm()
        form_imagenes = ImagenesDescargadasForm()
        return render(
            request, 
            'maps.html',
            {'form': form,
            'form_imagenes': form_imagenes}
        )
      else: 

        try:
          geometria = json.loads(request.POST.get('geometria'))
        except Exception as e:
          pass
        
        satelite = Satelite.objects.get(id=request.POST.get('satelite'))
        tipoImagen = Tipo_Imagen.objects.get(id=request.POST.get('tipoImagen'))
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        porcentaje= 0
        if( request.POST.get('geometria') == 'Shapefile cargado.'):
        #determinar si existen archivos subidos
          try:
            for uploaded_file in request.FILES.getlist('shapefiles'):
              handle_uploaded_file(uploaded_file)
            shp_file = get_shp_file(request.FILES.getlist('shapefiles'))
            
            geoms = process_shapefile("./temp_shapefiles/" + str(shp_file))
            for sq in geoms:
              xx, yy = sq.exterior.coords.xy
              x = xx.tolist()
              y = yy.tolist()
            geometria = list(zip(x,y))
            
          except Exception as e:
            # Manejo de excepciones genéricas (captura cualquier excepción no manejada anteriormente)
            print(f"Error: {e}")

        
        
        if satelite.name == 'Landsat8':
          url = descargar_imagen_landsat8(geometria, fecha_inicio, fecha_fin, tipoImagen)
          porcentaje = calcular_porcentaje_bosque(geometria, fecha_inicio, fecha_fin)
        elif satelite.name == 'Landsat7':
          url = descargar_imagen_landsat7(geometria, fecha_inicio, fecha_fin, tipoImagen)
        elif satelite.name == 'Sentinel-2':
          url = descargar_imagen_sentinel(geometria, fecha_inicio, fecha_fin, tipoImagen, 1500)
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
          'titulo': request.POST.get('titulo'),
          'porcentaje': porcentaje
          }
        )
 
  else:
    form = DescargaImagenForm()
    form_imagenes = ImagenesDescargadasForm()
    return render(
        request, 
        'maps.html',
        {'form': form,
         'form_imagenes': form_imagenes}
      )
  

def vista_satelite(request, url):
  return render(
        request, 
        'visualizar_imagen.html',
        {'url': url}
  )

def evaluacion(request):
   print(request.POST)
   return render(
     request,
     'evaluacion.html',
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
  extension = 'png'

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

  
  url = final_image.clip(geometry).getThumbUrl({'min': 0, 'max': 0.3, 'gamma': 1.4, 'bands': band, 'format': 'png'})
  
  
  return url
  

def descargar_imagen_sentinel(geometry, fecha_inicio, fecha_fin, tipoImagen, dimension):
  
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
  extension = 'png'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': dimension, 'format': extension })
  
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
    polygon = Polygon(tuple(geometry))
    gdf = gpd.GeoDataFrame({'geometry': [polygon]})
    ruta_guardar = 'shapefiles/nombre_shapefile.shp'
    gdf.to_file(ruta_guardar)
    return ruta_guardar

def divisionPoligonos(geo_path, satelite, fecha_inIcio, fecha_fin, tipo_imagen, pk_imagen, request, titulo):
    
    GeoDF = gpd.read_file(geo_path)

    
    G = np.random.choice(GeoDF.geometry.values)

    Rectangle = G.envelope

    # Longitud del lado de la celda
    side_length = 0.02

    
    rect_coords = np.array(Rectangle.boundary.coords.xy)

    
    y_list = rect_coords[1]
    x_list = rect_coords[0]

   
    y1 = min(y_list)
    y2 = max(y_list)

   
    x1 = min(x_list)
    x2 = max(x_list)

    
    width = x2 - x1
    height = y2 - y1

    
    xcells = int(np.round(width / side_length))
    ycells = int(np.round(height / side_length))

    
    yindices = np.linspace(y1, y2, ycells + 1)
    xindices = np.linspace(x1, x2, xcells + 1)

 
    horizontal_splitters = [
        LineString([(x, yindices[0]), (x, yindices[-1])]) for x in xindices
    ]

   
    vertical_splitters = [
        LineString([(xindices[0], y), (xindices[-1], y)]) for y in yindices
    ]

    
    result = Rectangle

  
    for splitter in vertical_splitters:
        result = MultiPolygon(split(result, splitter))

    
    for splitter in horizontal_splitters:
        result = MultiPolygon(split(result, splitter))

    
    square_polygons = list(result.geoms)
    

    
    df = gpd.GeoDataFrame(square_polygons)

    
    SquareGeoDF  = gpd.GeoDataFrame(square_polygons).rename(columns={0: "geometry"})

    
    SquareGeoDF = gpd.GeoDataFrame(square_polygons)

    
    SquareGeoDF = SquareGeoDF.set_geometry(0)


    
    Geoms = SquareGeoDF[SquareGeoDF.intersects(G)].geometry.values

    
    shape = "square"


    thresh = 0.2

    # Si la variable 'shape' es igual a "rhombus", realiza las siguientes operaciones.
    if shape == "rhombus":
        # Aplica una función 'rhombus(g)' a cada geometría en 'Geoms' y almacena los resultados en 'Geoms'.
        #Geoms = [rhombus(g) for g in Geoms]
        # Filtra las geometrías en 'Geoms' que cumplen con una condición de área y las almacena en 'geoms'.
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]
    elif shape == "square":
        
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]

    print(len(geoms))
    
    index = 1
    for sq in geoms:
      xx, yy = sq.exterior.coords.xy
      x = xx.tolist()
      y = yy.tolist()
      url = descargar_imagen_sentinel(list(zip(x,y)), fecha_inIcio, fecha_fin, tipo_imagen, 700)
      print(f"Imagen {index}: {url}")
      response = requests.get(url)
      if response.status_code == 200:
        #guardar sub imagen
        imagen_bytes = response.content
        imagen = ImagenSatelital.objects.get(pk=pk_imagen)
        subImagen = SubImagenSatelital.objects.create(   
            imagen=imagen,
            coordenadas=list(zip(x,y))
        )
        nombre_imagen = "Sub_" + titulo+ "_" +satelite.name + "_" + fecha_inIcio + "_" + fecha_fin + "_"+ str(index) +".png"
        subImagen.subImagen.save( nombre_imagen, ContentFile(imagen_bytes), save=True)
       
      else:
        form = DescargaImagenForm()
        form_imagenes = ImagenesDescargadasForm()
        return render(
            request, 
            'maps.html',
            {'form': form,
            'form_imagenes': form_imagenes}
        )
      index += 1
    
    #print(geoms)
    grid = gpd.GeoDataFrame({'geometry':geoms})



def get_shp_file(files):
    for uploaded_file in files:
        if uploaded_file.name.endswith('.shp'):
            return uploaded_file
    return None

def handle_uploaded_file(f):
    temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp_shapefiles')
    os.makedirs(temp_folder, exist_ok=True)  # Crea la carpeta temporal si no existe
    file_path = os.path.join(temp_folder, f.name)  # Conserva el nombre original del archivo
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path

def process_shapefile(file):
    print(file)
    gdf = gpd.read_file(file)
    geometries = gdf.geometry  
    return geometries
  
def eliminar_contenido_carpeta(carpeta_a_eliminar ):
    if os.path.exists(carpeta_a_eliminar):
        for contenido in os.listdir(carpeta_a_eliminar):
            contenido_ruta = os.path.join(carpeta_a_eliminar, contenido)
            if os.path.isfile(contenido_ruta):
                os.remove(contenido_ruta)      
            elif os.path.isdir(contenido_ruta):
                shutil.rmtree(contenido_ruta)
        os.rmdir(carpeta_a_eliminar)
    else:
        print(f"La carpeta '{carpeta_a_eliminar}' no existe.")