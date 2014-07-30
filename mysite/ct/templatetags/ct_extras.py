from django.utils.safestring import mark_safe
from markdown import markdown
from django import template

register = template.Library()

@register.filter(name='md2html')
def md2html(txt):
    return mark_safe(markdown(txt, safe_mode='escape'))

