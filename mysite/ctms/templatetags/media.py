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
