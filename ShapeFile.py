import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.13797980357646,-36.720316313773154],[-73.08128083041682,-36.69870692604257],[-72.97160084955114,-36.723296442044685],[-72.97085725646065,-36.76024042484195],[-73.11938997631094,-36.78332138244232],[-73.13797980357646,-36.720316313773154]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
