import geopandas as gpd
from shapely.geometry import Polygon

# Crea una geometría (en este caso, un polígono)
polygon = Polygon([[-73.04142982734002,-36.807703524090286],[-73.00229103339437,-36.80316784260404],[-72.99722702277442,-36.8230266421785],[-73.02838356269123,-36.84095697822952],[-73.05190117133367,-36.82666800831895],[-73.04142982734002,-36.807703524090286]])

# Crea un GeoDataFrame con la geometría
gdf = gpd.GeoDataFrame({'geometry': [polygon]})

# Define la ruta donde deseas guardar el archivo shapefile
ruta_guardar = 'shapefiles/nombre_shapefile.shp'

# Guarda el GeoDataFrame como un archivo shapefile
gdf.to_file(ruta_guardar)

print(f'Shapefile guardado en: {ruta_guardar}')
