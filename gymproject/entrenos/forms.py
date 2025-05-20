from django import forms
from clientes.models import Cliente
from rutinas.models import Ejercicio
from .models import DetalleEjercicioRealizado
from clientes.models import Cliente


class FiltroClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=False,
        label="Filtrar por cliente",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class SeleccionClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Selecciona un cliente"
    )


class DetalleEjercicioForm(forms.Form):
    ejercicio_id = forms.IntegerField(widget=forms.HiddenInput())
    series = forms.IntegerField(min_value=1, label="Series")
    repeticiones = forms.IntegerField(min_value=1, label="Repeticiones")
    peso_kg = forms.DecimalField(min_value=0, max_digits=5, decimal_places=2, label="Peso (kg)")
    completado = forms.BooleanField(required=False, initial=True, label="¿Completado?")
