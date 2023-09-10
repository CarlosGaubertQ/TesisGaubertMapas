import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.15398858746755,-36.70643089922246],[-73.11974214276574,-36.70656852149412],[-73.12017129620828,-36.72363177314512],[-73.15707849225248,-36.72370056890712],[-73.15398858746755,-36.70643089922246]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
