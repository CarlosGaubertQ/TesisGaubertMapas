import ee

# Inicializa el entorno Earth Engine
ee.Initialize()

# Define la región de interés (aoi)
aoi = ee.Geometry.Polygon(
        [[[-120.23666381835938, 38.2068653630926],
          [-120.23666381835938, 36.86048636181168],
          [-118.06060791015625, 36.86048636181168],
          [-118.06060791015625, 38.2068653630926]]])

# Filtra la colección de imágenes Landsat 7
l7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")
      .filterDate('2004-01-01', '2004-12-31')
      .filterBounds(aoi)
      .sort('CLOUD_COVER', True)
      .first())

# Calcula el promedio focal
img_fill = l7.focal_mean(1, 'square', 'pixels', 8)

# Combina la imagen promedio con la imagen Landsat 7 original
final_image = img_fill.blend(l7)

# Define el estilo para la visualización
l7_style = {"bands": ["B3", "B2", "B1"], "min": 0.0265324916690588, "max": 0.256043404340744, "gamma": 1}

# Obtiene una URL para la imagen en formato JPG
image_url = final_image.clip(aoi).getThumbUrl({'min': 0, 'max': 0.3, 'gamma': 1.4, 'bands': 'B3,B2,B1', 'format': 'jpg'})

print("URL de la imagen en formato JPG:", image_url)
