from django import template
register = template.Library()


@register.filter(name='get')
def get(value, arg):
    return value.get(arg)
