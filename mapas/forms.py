from . import models
from django.forms import ModelForm
from django import forms

class SateliteForm(ModelForm):
    class Meta:
        model = models.Satelite
        fields = ['name']


class TipoImagenForm(ModelForm):
    class Meta:
        model = models.Tipo_Imagen
        fields = ['name']

class DescargaImagenForm(forms.Form):
    latitud = forms.FloatField(label="Latitud", widget=forms.TextInput(attrs={'class': 'form-control'}))
    longitud = forms.FloatField(label="Longitud",widget=forms.TextInput(attrs={'class': 'form-control'}))
    satelite = forms.ModelChoiceField(label="Satelite", queryset=models.Satelite.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    tipoImagen = forms.ModelChoiceField(label="Tipo de imagen", queryset=models.Tipo_Imagen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))