from . import models
from django.forms import ModelForm
from django import forms
from multiupload.fields import MultiFileField

class SateliteForm(ModelForm):
    class Meta:
        model = models.Satelite
        fields = ['name']


class TipoImagenForm(ModelForm):
    class Meta:
        model = models.Tipo_Imagen
        fields = ['name']

class DescargaImagenForm(forms.Form):
    geometria = forms.FloatField(label="Geometria", widget=forms.TextInput(attrs={'class': 'form-control'}))
    shapefiles = MultiFileField(min_num=1, max_num=20, max_file_size=1024*1024*5, required=False)  # Hasta 5 MB por archivo y hasta 20 archivos
    satelite = forms.ModelChoiceField(label="Satelite", queryset=models.Satelite.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    tipoImagen = forms.ModelChoiceField(label="Tipo de imagen", queryset=models.Tipo_Imagen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_inicio = forms.DateField(
        label='Fecha de inicio',
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        label='Fecha de fin',
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    metros_cuadrados = forms.FloatField(
        label="Metros cuadrados",
        widget=forms.TextInput(attrs={'class': 'form-control','readonly': 'readonly'})
    )

