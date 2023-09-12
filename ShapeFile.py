import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.12427104019815,-36.70832883454821],[-73.0155264326096,-36.709000733960224],[-72.97404005052361,-36.74342771194787],[-73.01825028597877,-36.77800707697108],[-73.12217576837543,-36.76894409098962],[-73.15695728062938,-36.744099304340736],[-73.12427104019815,-36.70832883454821]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
