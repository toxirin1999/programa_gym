from django import template

register = template.Library()


@register.filter
def make_range(value):
    try:
        return range(int(value))
    except:
        return range(0)
