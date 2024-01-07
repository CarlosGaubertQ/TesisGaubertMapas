
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
from io import BytesIO

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
        calcular_porcentaje_bosques(request)
        #guardar imagen en la base de datos
        """
        fechas_dict = [2018, 2019, 2020, 2021]
        
        for i, fecha in enumerate(fechas_dict):
          start_date = str(fecha) + "-01-01" 
          fecha += 1
          end_date = str(fecha) + "-01-01" 
          url = descargar_imagen_sentinel(json.loads(request.POST.get('geometria')), start_date, end_date,Tipo_Imagen.objects.get(id=request.POST.get('tipoImagen')) , 1500)
          print(f"[INFO] Imagen {i+1} url: {url}")
          response = requests.get(url)

          if response.status_code == 200:
              
              
              
              print(f"[INFO] Guardando imagen {i+1} en la base de datos ")
              satelite = Satelite.objects.get(pk=request.POST.get('satelite'))
              
              imagen_bytes = response.content
              
              tipo_imagen = Tipo_Imagen.objects.get(pk=request.POST.get('tipoImagen'))
              
              titulo = request.POST.get('titulo')
              nombre_imagen = titulo +"_" + satelite.name + "_" + start_date + "_" + end_date +".png"
              imagen = ImagenSatelital.objects.create(
                  name=nombre_imagen,
                  coordenadas=request.POST.get('geometria'),
                  satelite=satelite,
                  tipo_imagen=tipo_imagen,
              )
              imagen.imagen.save( nombre_imagen, ContentFile(imagen_bytes), save=True)

              imagen.save()
              

                
              
              #divisionPoligonos(geo_path, satelite, request.POST.get('fecha_inicio'), request.POST.get('fecha_fin'), tipo_imagen, imagen.pk,request, titulo)
        else:
          form = DescargaImagenForm()
          form_imagenes =ImagenesDescargadasForm()
          return render(
            request, 
            'maps.html',
            {'form': form,
            'form_imagenes': form_imagenes}
          )
        """

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

        geo_path = crear_archivo_shapefile(geometria)
        print(f"Generando archivo shapefile en {geo_path}")
        
        

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

def crear_archivo_shapefile(geometry):
    polygon = Polygon(tuple(geometry))
    gdf = gpd.GeoDataFrame({'geometry': [polygon]})
    ruta_guardar = 'shapefiles/nombre_shapefile.shp'
    gdf.to_file(ruta_guardar)
    return ruta_guardar




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



#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################
#################################################################################################


import numpy as np
from shapely.ops import split
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon, LineString
import ee
import requests
import os
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import shutil
import torchvision
import rasterio
import rasterio.plot
import matplotlib.pyplot as plt
import cv2
from rasterio.features import geometry_mask
from shapely.geometry import mapping
from torchvision import models, transforms
import torch.nn.functional as F  # Import functional interface
from PIL import Image
from torch import nn
import torch
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import time

def export_rectangle_to_drive(Rectangle, name_file, start_date, end_date):
    ee.Initialize()
    """
    Exports the envelope of a geometry from a shapefile to Google Drive.

    Args:
    - geo_filepath (str): Path to the shapefile.
    - scale (int): Resolution scale. Default is 10 for Sentinel-2.

    Returns:
    - str: Status of the export task.
    """

    # Convert the shapely geometry to an Earth Engine Geometry
    coords = list(Rectangle.exterior.coords)
    region = ee.Geometry.Polygon(coords)

    # Define the image collection for Sentinel-2 and filter by the region
    collection = ee.ImageCollection('COPERNICUS/S2') \
        .filterDate(start_date,end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .filterBounds(region) \

    # Get the first image from the collection
    image = collection.median().select(['B4', 'B3', 'B2'])  # RGB bands for Sentinel-2

    # Define export parameters
    task_config = {
        'description': name_file,
        'folder': 'rasters',
        'fileNamePrefix': name_file, 
        'scale': 10,
        'region': region,
        'maxPixels': 1e13  # Increase this if you get an error related to pixel count
    }

    # Start the export task to Google Drive
    task = ee.batch.Export.image.toDrive(image, **task_config)
    task.start()

    return task

def check_task_status(task):
    return task.status()

def get_file_id_by_name(filename, drive):
    """
    Get the file ID of a file in Google Drive based on its name.

    Args:
    - filename (str): The name of the file.

    Returns:
    - str: The file ID or None if not found.
    """
 
    # Search for the file by its name
    file_list = drive.ListFile({'q': f"title='{filename}'"}).GetList()

    # If the file is found, return its ID
    for file in file_list:
        if file['title'] == filename:
            return file['id']
    return None

def extract_patch_from_masked_data(red_clip, green_clip, blue_clip, mask):
    # Find where the mask is True
    rows, cols = np.where(mask)

    # Get the bounding box coordinates
    top_row = np.min(rows)
    bottom_row = np.max(rows)
    left_col = np.min(cols)
    right_col = np.max(cols)

    # Extract the patch using the bounding box
    red_patch = red_clip[top_row:bottom_row+1, left_col:right_col+1]
    green_patch = green_clip[top_row:bottom_row+1, left_col:right_col+1]
    blue_patch = blue_clip[top_row:bottom_row+1, left_col:right_col+1]

    return red_patch, green_patch, blue_patch

def calcular_porcentaje_bosques(request):
    # Autenticación
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Se abrirá una ventana del navegador para autenticación

    # Crear un objeto de GoogleDrive utilizando la autenticación
    drive = GoogleDrive(gauth)
    

    id_carpeta = '1TvcWff-3Qt-U7WFuzRDRRbnP3UHHezVB'

    archivos_en_carpeta = drive.ListFile({'q': f"'{id_carpeta}' in parents and trashed=false"}).GetList()

    for archivo in archivos_en_carpeta:
        try:
            archivo.Delete()
            print(f"Archivo '{archivo['title']}' eliminado correctamente.")
        except:
            print(f"No se pudo eliminar el archivo '{archivo['title']}'.")

    print("Archivos en la carpeta eliminados correctamente.")

    
    # obtener geometria
    geo_filepath = "./shapefiles/nombre_shapefile.shp"
    GeoDF = gpd.read_file(geo_filepath)
    G = np.random.choice(GeoDF.geometry.values)
    Rectangle = G.envelope
    
    # Call the function
    fechas_dict = [2018, 2019, 2020, 2021]

    for i, fecha in enumerate(fechas_dict):
        start_date = str(fecha) + "-01-01" 
        fecha += 1
        end_date = str(fecha) + "-01-01" 
        name_file =  f"RectangleExport_{i+1}"
        if(i == 0):
          task = export_rectangle_to_drive(Rectangle,name_file=name_file,start_date=start_date, end_date=end_date)
        elif(i == 1):
          task1 = export_rectangle_to_drive(Rectangle,name_file=name_file,start_date=start_date, end_date=end_date)
        elif(i == 2):
          task2 = export_rectangle_to_drive(Rectangle,name_file=name_file,start_date=start_date, end_date=end_date) 
        elif(i == 3):
          task3 = export_rectangle_to_drive(Rectangle,name_file=name_file,start_date=start_date, end_date=end_date) 

    while task.active():
        print("Polling for task (id: {}).".format(task.id))
        time.sleep(10)  # Wait for 5 minutes
        status = check_task_status(task)
        print(status)

    while task1.active():
        print("Polling for task (id: {}).".format(task1.id))
        time.sleep(10)  # Wait for 5 minutes
        status = check_task_status(task1)
        print(status)

    while task2.active():
        print("Polling for task (id: {}).".format(task2.id))
        time.sleep(10)  # Wait for 5 minutes
        status = check_task_status(task2)
        print(status)
        
    while task3.active():
        print("Polling for task (id: {}).".format(task3.id))
        time.sleep(10)  # Wait for 5 minutes
        status = check_task_status(task3)
        print(status)

    
    #Calcular division de geometrias
    rect_coords = np.array(Rectangle.boundary.coords.xy)
    y_list = rect_coords[1]
    x_list = rect_coords[0]
    y1 = min(y_list)
    y2 = max(y_list)
    x1 = min(x_list)
    x2 = max(x_list)
    width = x2 - x1
    height = y2 - y1
    xcells = int(width * 100)
    ycells = int(height * 100)
    yindices = np.linspace(y1, y2, ycells + 3)
    xindices = np.linspace(x1, x2, xcells + 5)
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
    SquareGeoDF  = gpd.GeoDataFrame(square_polygons).rename(columns={0: "geometry"})
    SquareGeoDF = gpd.GeoDataFrame(square_polygons)

    SquareGeoDF = SquareGeoDF.set_geometry(0)

    Geoms = SquareGeoDF[SquareGeoDF.intersects(G)].geometry.values
    shape = "square"
    thresh = 0.9

    if shape == "rhombus":
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]
    elif shape == "square":
        geoms = [g for g in Geoms if ((g.intersection(G)).area / g.area) >= thresh]
    
    class_id_to_label = {
        0: "ann_crop",
        1: "forest",
        2: "herb_veg",
        3: "highway",
        4: "industrial",
        5: "pasture",
        6: "perm_crop",
        7: "residential",
        8: "river",
        9: "sea_lake"
    }
    class_id_to_color = {
        0: (0, 0, 255),  # Red
        1: (0, 143, 57),  # Blue
        2: (0, 255, 0),  # Green
        3: (0, 255, 255),  # Yellow
        4: (0, 165, 255),  # Orange
        5: (128, 0, 128),  # Purple
        6: (145, 176, 255),  # Cyan
        7: (255, 0, 255),  # Magenta
        8: (128, 0, 0),  # Brown
        9: (235, 206, 135)  # Lime
    }
    # Setup device agnostic code
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Load Model
    path = './models/ViT_Satellite.pth'
    # 1. Get pretrained weights for ViT-Base
    model_weights = torchvision.models.ViT_B_16_Weights.DEFAULT # requires torchvision >= 0.13, "DEFAULT" means best available


    # Get automatic transforms from pretrained ViT weights
    transform_im = model_weights.transforms()
    print(transform_im)

    # 2. Setup a ViT model instance with pretrained weights
    model = torchvision.models.vit_b_16(weights=model_weights).to(device)


    # 3. Freeze the base parameters
    for parameter in model.parameters():
        parameter.requires_grad = False

    # 4. Change the classifier head (set the seeds to ensure same initialization with linear head)
    model.heads = nn.Linear(in_features=768, out_features=10).to(device)
    model.load_state_dict(torch.load(path, map_location='cpu'))

    # Usage
    for i, fecha in enumerate(fechas_dict):
        file_id = get_file_id_by_name(f'RectangleExport_{i+1}.tif', drive)

        downloaded = drive.CreateFile({'id': file_id})
        downloaded.GetContentFile(f'downloaded_image_{i+1}.tif')
    for i, fecha in enumerate(fechas_dict):
        model.eval()

        bboxes = []
        with rasterio.open(f'downloaded_image_{i+1}.tif') as src:
            # Read the RGB bands
            red = src.read(1)
            green = src.read(2)
            blue = src.read(3)
            transform = src.transform
            

            full_mask = np.zeros_like(red, dtype=bool)
            forest = 0
            
            for i, polygon in enumerate(geoms):
                
                # Convert to pixel coordinates
                pixel_polygon = [~transform * (x, y) for x, y in polygon.exterior.coords]
                
                # Create a mask for the polygon
                geojson_polygon = mapping(polygon)
                mask = geometry_mask([geojson_polygon], transform=transform, invert=True, out_shape=src.shape)
                full_mask = np.logical_or(full_mask, mask)
                
                red_clip = src.read(1) * mask
                green_clip = src.read(2) * mask
                blue_clip = src.read(3) * mask

                red_patch, green_patch, blue_patch = extract_patch_from_masked_data(red_clip, green_clip, blue_clip, mask)

                pixel_shapely_polygon = Polygon(pixel_polygon)
                x1, y1, x2, y2 = pixel_shapely_polygon.bounds
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
                
                bands_8bit = []
                for band_name in [red_patch, green_patch, blue_patch]:
                    band_data = band_name
                    min_val = 0
                    max_val = 2750
                    band_8bit = ((band_data - min_val) / (max_val - min_val)) * 255
                    band_8bit = np.clip(band_8bit, 0, 255).round().astype(np.uint8)
                    bands_8bit.append(band_8bit)

                data_8bit = np.stack(bands_8bit, axis=-1)

                # Inference

                pil_image = Image.fromarray(data_8bit)
                tensor_im  = transform_im(pil_image).unsqueeze(0)

                with torch.no_grad():
                    outputs = model(tensor_im.to(device))
                    
                    # Convert raw output scores to probabilities
                    probabilities = F.softmax(outputs, dim=1)
                    
                    # Get the predicted class and its probability
                    _, preds = torch.max(outputs, 1)
                    pred_class = preds.item()
                    pred_prob = probabilities[0][pred_class].item()

                    bboxes.append([pred_class, pred_prob, x1, y1, x2, y2])

                    #print(f"Predicted class: {class_id_to_label[pred_class]}, clase:{pred_class} , x1: {x1}, y1: {y1}, x2:{x2}, y2:{y2}, shape image: {(x2-x1, y2-y1)}")

                    if pred_class == 1:
                        forest += 1
                
            # Save or visualize the clipped image

            # Apply the mask to the RGB bands
            red_masked = np.where(full_mask, red, 0)
            green_masked = np.where(full_mask, green, 0)
            blue_masked = np.where(full_mask, blue, 0)

            bands_8bit = []
            for band_name in [red_masked, green_masked, blue_masked]:
                band_data = band_name
                min_val = 0
                max_val = 2750 #band_data.max()
                band_8bit = ((band_data - min_val) / (max_val - min_val)) * 255
                band_8bit = np.clip(band_8bit, 0, 255).round().astype(np.uint8)
                bands_8bit.append(band_8bit)

            data_8bit = np.stack(bands_8bit, axis=-1)

            satelite = Satelite.objects.get(pk=request.POST.get('satelite'))
            
            start_date = str(fecha) + "-01-01" 
            fecha += 1
            end_date = str(fecha) + "-01-01" 
            
            tipo_imagen = Tipo_Imagen.objects.get(pk=request.POST.get('tipoImagen'))
            
            titulo = request.POST.get('titulo')
            nombre_imagen = titulo +"_" + satelite.name + "_" + start_date + "_" + end_date +".png"
            imagen = ImagenSatelital.objects.create(
                name=nombre_imagen,
                coordenadas=request.POST.get('geometria'),
                satelite=satelite,
                tipo_imagen=tipo_imagen,
            )
            imagen.imagen.save( nombre_imagen, ContentFile(cv2.cvtColor(data_8bit, cv2.COLOR_RGB2BGR)), save=True)

            imagen.save()
            cv2.imwrite(f"./imagenes/{nombre_imagen}", cv2.cvtColor(data_8bit, cv2.COLOR_RGB2BGR))
            #cv2.imwrite(f'full_geom.png', cv2.cvtColor(data_8bit, cv2.COLOR_RGB2BGR))
            print(f"Porcentaje de bosques en imagen para el año {start_date}: {(forest / len(geoms))* 100:.2f}%")

