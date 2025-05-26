from django import forms
from .models import Cliente, Medida
from .models import RevisionProgreso
from django.db import models
from .models import ObjetivoCliente
from django import forms
from .models import DietaAsignada

from django import forms


class DatosNutricionalesForm(forms.Form):
    edad = forms.IntegerField(label="Edad", min_value=1, max_value=120)
    genero = forms.ChoiceField(label="Género", choices=[('M', 'Masculino'), ('F', 'Femenino')])
    altura_cm = forms.DecimalField(label="Altura (cm)", max_digits=5, decimal_places=2, min_value=50)
    peso_kg = forms.DecimalField(label="Peso (kg)", max_digits=5, decimal_places=2, min_value=20)

    NIVEL_ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario (poco o ningún ejercicio)'),
        ('levemente_activo', 'Levemente activo (ejercicio ligero/deporte 1-3 días/semana)'),
        ('moderadamente_activo', 'Moderadamente activo (ejercicio moderado/deporte 3-5 días/semana)'),
        ('muy_activo', 'Muy activo (ejercicio intenso/deporte 6-7 días/semana)'),
        ('extremadamente_activo', 'Extremadamente activo (ejercicio muy intenso/trabajo físico)'),
    ]
    nivel_actividad = forms.ChoiceField(label="Nivel de Actividad Física", choices=NIVEL_ACTIVIDAD_CHOICES)

    OBJETIVO_CHOICES = [
        ('masa_muscular', 'Ganar Masa Muscular'),
        ('definir', 'Definir / Mantener Peso'),
        ('perder_peso', 'Perder Peso'),
    ]
    objetivo = forms.ChoiceField(label="Objetivo", choices=OBJETIVO_CHOICES)

    # Puedes añadir más campos para preferencias dietéticas si lo deseas
    # comidas_dia = forms.IntegerField(label="Número de comidas al día deseadas", min_value=2, max_value=6, required=False)
    # restricciones_dieteticas = forms.CharField(label="Restricciones o preferencias dietéticas (ej. vegetariano, sin lactosa)", widget=forms.Textarea, required=False)


class DietaAsignadaForm(forms.ModelForm):
    class Meta:
        model = DietaAsignada
        fields = ['dieta', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class ObjetivoClienteForm(forms.ModelForm):
    class Meta:
        model = ObjetivoCliente
        fields = ['medida', 'valor']
        error_messages = {
            'medida': {
                'required': 'Selecciona una medida.',
            },
            'valor': {
                'required': 'Debes ingresar un valor objetivo.',
            },
        }

    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        self.instancia = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        medida = cleaned_data.get('medida')

        if not self.cliente or not medida:
            return

        existe = ObjetivoCliente.objects.filter(cliente=self.cliente, medida=medida)
        if self.instancia:
            existe = existe.exclude(pk=self.instancia.pk)

        if existe.exists():
            raise forms.ValidationError(f"Ya existe un objetivo para {self.cliente.nombre} con la medida '{medida}'.")

        return cleaned_data


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
            'biceps', 'antebrazos', 'caderas', 'muslos', 'gemelos', 'proximo_registro_peso', 'foto'
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
