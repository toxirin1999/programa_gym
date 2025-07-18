from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def replace(value, arg):
    """
    Reemplaza una subcadena por otra en una cadena de texto.
    Uso: {{ "Hola Mundo"|replace:"Mundo,Planeta" }}
    """
    try:
        old, new = arg.split(',')
        return value.replace(old, new)
    except (ValueError, TypeError):
        return value
