from django import template

register = template.Library()

@register.filter
def divide100(value):
    try:
        return round(value / 100, 2)
    except (TypeError, ValueError):
        return value