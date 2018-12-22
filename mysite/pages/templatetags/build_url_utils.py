from django import template
from core.common.utils import get_redirect_url


register = template.Library()


@register.simple_tag
def build_redirect_url(user):
    return get_redirect_url(user)
