import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-72.91243014072717,-36.697554715649254],[-72.83121410919405,-36.63388925272916],[-72.71861915638665,-36.679792907769844],[-72.63740312485302,-36.67929946565827],[-72.63801839781951,-36.767082284971266],[-72.88658867614858,-36.77151807695173],[-72.97457271030983,-36.742434323596484],[-72.91243014072717,-36.697554715649254]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
