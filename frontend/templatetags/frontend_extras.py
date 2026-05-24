from django import template

register = template.Library()


@register.filter
def get_item(value, key):
    if value is None:
        return None

    if hasattr(value, 'get'):
        return value.get(key)

    try:
        return value[key]
    except (TypeError, KeyError, IndexError):
        return None