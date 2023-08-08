from django.urls import path

from mapas.views import maps

urlpatterns = [
   path('', maps),

]