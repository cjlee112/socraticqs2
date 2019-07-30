from django import template


register = template.Library()


@register.simple_tag
def is_temporary(user):
    return user.groups.filter(name='Temporary').exists()
