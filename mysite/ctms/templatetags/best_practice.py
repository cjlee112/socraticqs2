from django import template
register = template.Library()


@register.filter(name='active')
def active(obj):
    return obj.filter(active=True)