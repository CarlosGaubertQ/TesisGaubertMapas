import ee
def calcular_porcentaje_bosque(geometry, fecha_inicio, fecha_fin):
    # Inicializar la API de Google Earth Engine
    ee.Initialize()

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

    return porcentaje_bosque

# Llamar a la función para calcular el porcentaje de bosque
ee.Initialize()
geometry = ee.Geometry.Polygon([[-122.36, 37.45], [-121.97, 37.45], [-121.97, 37.69], [-122.36, 37.69]])
fecha_inicio = '2022-01-01'
fecha_fin = '2022-12-31'

porcentaje = calcular_porcentaje_bosque(geometry, fecha_inicio, fecha_fin)
print(f'Porcentaje de bosque: {porcentaje * 100:.2f}%')