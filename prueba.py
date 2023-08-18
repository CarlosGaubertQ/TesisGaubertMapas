import matplotlib.pyplot as plt
import urllib.request
from matplotlib.image import imread

# URL de la imagen que deseas visualizar
image_url = "https://www.smashbros.com/images/og/sonic.jpg"

# Descargar la imagen desde la URL
image = imread(urllib.request.urlopen(image_url), format='jpg')

# Mostrar la imagen utilizando Matplotlib
plt.imshow(image)
plt.axis('off')  # Ocultar los ejes
plt.show()