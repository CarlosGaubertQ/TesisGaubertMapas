import ee

def descargar_imagen_landsat(geometry, fecha_inicio, fecha_fin):
  # Filtrar la colección de imágenes Landsat 8

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


  imagenRGB = Landsat8Clip.visualize(**{'min': 0,'max': 0.5, 'bands': ['B4', 'B3', 'B2']})
  extension = 'png'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
  print(url)
  return url
  
  



def descargar_imagen_sentinel(geometry, fecha_inicio, fecha_fin):
  print(geometry)
  
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
  imagenRGB = datasetClip.visualize(**{'min': 0,'max': 2500, 'bands': ['B4', 'B3', 'B2']})
  extension = 'jpg'

  url = imagenRGB.getThumbURL({ 'region': geometry, 'dimensions': 500, 'format': extension })
  print(url)
  return url
   
