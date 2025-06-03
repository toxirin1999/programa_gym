from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def porcentaje(valor, total):
    """
    Calcula el porcentaje de un valor respecto a un total.
    
    Uso: {{ valor|porcentaje:total }}
    """
    if total == 0:
        return 0
    return min(100, int((valor / total) * 100))

@register.filter
def add_days(date, days):
    """
    Añade un número de días a una fecha.
    
    Uso: {{ fecha|add_days:7 }}
    """
    return date + timedelta(days=days)

@register.filter
def timeuntil(date1, date2):
    """
    Calcula el tiempo restante entre dos fechas en formato legible.
    
    Uso: {{ fecha1|timeuntil:fecha2 }}
    """
    if not date1 or not date2:
        return ""
    
    delta = date2 - date1
    days = delta.days
    
    if days <= 0:
        return "hoy"
    elif days == 1:
        return "1 día"
    elif days < 7:
        return f"{days} días"
    elif days < 14:
        return "1 semana"
    elif days < 30:
        return f"{days // 7} semanas"
    elif days < 60:
        return "1 mes"
    else:
        return f"{days // 30} meses"
