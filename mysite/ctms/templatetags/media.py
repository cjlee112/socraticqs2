import os

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def media_prefix(context, value):
    url = '#'
    try:
        url = value.url
    except (ValueError, AttributeError):
        pass
    return url


@register.filter()
def is_svg(value):
    _, file_extension = os.path.splitext(value.name)
    return file_extension == '.svg'
