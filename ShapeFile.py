import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.15285324738679,-36.702637284934106],[-73.1208384005849,-36.70167387457427],[-73.10882210419877,-36.720045405383885],[-73.07654976533122,-36.731602768665695],[-73.08856606171811,-36.74198915254975],[-73.12195419953564,-36.74240182751606],[-73.13843369172312,-36.72795688353061],[-73.15242409394426,-36.726443446405824],[-73.1564581363031,-36.716467773785546],[-73.15285324738679,-36.702637284934106]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
