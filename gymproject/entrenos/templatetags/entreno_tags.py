from django import template

register = template.Library()


@register.filter
def sum_volumen(series):
    """Calcula el volumen total (peso × repeticiones) para un conjunto de series"""
    return sum(serie.peso_kg * serie.repeticiones for serie in series)
