from django.utils.safestring import mark_safe
from markdown import markdown
from django import template
import re

register = template.Library()

InlineMathPat = re.compile(r'\\\((.+?)\\\)', flags=re.DOTALL)
DisplayMathPat = re.compile(r'\\\[(.+?)\\\]', flags=re.DOTALL)

@register.filter(name='md2html')
def md2html(txt, stripP=False):
    'convert markdown to html, preserving latex delimiters'
    # markdown replaces \( with (, so have to protect our math...
    # replace \(math\) with \\(math\\)
    txt = InlineMathPat.sub(r'\\\\(\1\\\\)', txt)
    # replace \[math\] with \\[math\\]
    txt = DisplayMathPat.sub(r'\\\\[\1\\\\]', txt)
    txt = markdown(txt, safe_mode='escape')
    if stripP and txt.startswith('<p>') and txt.endswith('</p>'):
        txt = txt[3:-4]
    return mark_safe(txt)

