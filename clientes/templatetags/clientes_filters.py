from django import template

register = template.Library()


@register.filter(name='humanize_number')
def humanize_number(value):
    """
    Convierte un número grande en un formato legible por humanos.
    Ej: 1234 -> 1.2 K, 1234567 -> 1.2 M
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    if value < 1000:
        return str(value)
    elif value < 1000000:
        # Formato K (miles) con un decimal
        return f'{value / 1000:.1f} K'.replace('.0', '')
    elif value < 1000000000:
        # Formato M (millones) con un decimal
        return f'{value / 1000000:.1f} M'.replace('.0', '')
    else:
        # Formato B (billones) con un decimal
        return f'{value / 1000000000:.1f} B'.replace('.0', '')
