from django import forms
from .models import Programa, Ejercicio, Rutina, RutinaEjercicio


class RutinaEjercicioForm(forms.ModelForm):
    ejercicio = forms.ModelChoiceField(
        queryset=Ejercicio.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Selecciona un ejercicio"
    )

    class Meta:
        model = RutinaEjercicio
        fields = ['ejercicio', 'series', 'repeticiones', 'peso_kg']
        widgets = {
            'series': forms.NumberInput(attrs={'class': 'form-control'}),
            'repeticiones': forms.NumberInput(attrs={'class': 'form-control'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EjercicioForm(forms.ModelForm):
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'grupo_muscular', 'equipo']


class RutinaForm(forms.ModelForm):
    ejercicios = forms.ModelMultipleChoiceField(
        queryset=Ejercicio.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Ejercicios disponibles"
    )

    class Meta:
        model = Rutina
        fields = ['nombre', 'ejercicios']
