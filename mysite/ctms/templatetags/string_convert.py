from django import template


register = template.Library()


@register.filter(name='decode')
def decode(value):
    return value.decode('utf-8')
