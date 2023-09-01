import ee

# Inicializa Earth Engine
ee.Initialize()

# Crea una geometría (en este caso, un polígono)
geometry = ee.Geometry.Polygon(
    [[[-74.05, 40.7],
      [-74.05, 40.8],
      [-73.95, 40.8],
      [-73.95, 40.7]]])

# Exporta la geometría a un shapefile
task = ee.batch.Export.table.toDrive(
    collection=ee.FeatureCollection(geometry),
    description='nombre_del_shapefile',
    folder='./TesisGaubert/',
    fileFormat='SHP')

# Inicia la tarea de exportación
task.start()