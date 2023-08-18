from django.urls import path

from mapas.views import maps, vistaSatelite

urlpatterns = [
   path('', maps),
   path('vistasatelite/', vistaSatelite, name='vista_satelite')
 
]