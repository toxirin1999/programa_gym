from django import forms
from .models import ClienteDieta, Dieta, Comida


class ComidaForm(forms.ModelForm):
    class Meta:
        model = Comida
        fields = ['nombre', 'descripcion', 'hora_aproximada']


class DietaForm(forms.ModelForm):
    class Meta:
        model = Dieta
        fields = ['nombre', 'descripcion', 'calorias_totales']


class ClienteDietaForm(forms.ModelForm):
    class Meta:
        model = ClienteDieta
        fields = ['dieta', 'fecha_inicio', 'fecha_fin', 'observaciones']
