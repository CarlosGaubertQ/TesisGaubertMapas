import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.13105258175706, -36.705746266993266],
          [-73.13105258175706, -36.7745272641162],
          [-72.94256838986253, -36.7745272641162],
          [-72.94256838986253, -36.705746266993266]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
