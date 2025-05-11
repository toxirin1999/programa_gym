from django import forms
from .models import Cliente, Medida
from .models import RevisionProgreso
from django.db import models


class RevisionProgresoForm(forms.ModelForm):
    class Meta:
        model = RevisionProgreso
        fields = '__all__'
        exclude = ['cliente']  # si lo asignas desde la vista
        widgets = {
                      field: forms.NumberInput(attrs={'class': 'form-control'})
                      for field in model._meta.get_fields()
                      if isinstance(field, models.DecimalField) or isinstance(field, models.FloatField)
                  } | {
                      'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                  }


class MedidaForm(forms.ModelForm):
    class Meta:
        model = Medida
        fields = ['nombre', 'valor', 'unidad']


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'email', 'telefono', 'fecha_nacimiento', 'direccion', 'genero',
            'membresia_activa', 'fecha_vencimiento_membresia', 'programa',  # ✅ añadimos programa aquí
            'peso_corporal', 'grasa_corporal', 'cintura', 'pecho', 'hombro', 'cuello',
            'biceps', 'antebrazos', 'caderas', 'muslos', 'gemelos', 'foto'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'membresia_activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_vencimiento_membresia': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'programa': forms.Select(attrs={'class': 'form-select'}),  # ✅ widget para programa
            'peso_corporal': forms.NumberInput(attrs={'class': 'form-control'}),
            'grasa_corporal': forms.NumberInput(attrs={'class': 'form-control'}),
            'cintura': forms.NumberInput(attrs={'class': 'form-control'}),
            'pecho': forms.NumberInput(attrs={'class': 'form-control'}),
            'hombro': forms.NumberInput(attrs={'class': 'form-control'}),
            'cuello': forms.NumberInput(attrs={'class': 'form-control'}),
            'biceps': forms.NumberInput(attrs={'class': 'form-control'}),
            'antebrazos': forms.NumberInput(attrs={'class': 'form-control'}),
            'caderas': forms.NumberInput(attrs={'class': 'form-control'}),
            'muslos': forms.NumberInput(attrs={'class': 'form-control'}),
            'gemelos': forms.NumberInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
