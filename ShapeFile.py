import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-70.87614369062425,-33.367203239240126],[-70.40648291112873,-33.36158950122372],[-70.39989651400553,-33.59156471876422],[-70.86955729350106,-33.595300959866876],[-70.87614369062425,-33.367203239240126]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefilesForest/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
