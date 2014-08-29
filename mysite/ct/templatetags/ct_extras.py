from django.utils.safestring import mark_safe
from markdown import markdown
from django import template
import re
import pypandoc
from django.contrib.staticfiles.templatetags import staticfiles

register = template.Library()

InlineMathPat = re.compile(r'\\\((.+?)\\\)', flags=re.DOTALL)
DisplayMathPat = re.compile(r'\\\[(.+?)\\\]', flags=re.DOTALL)
StaticImagePat = re.compile(r'STATICIMAGE/([^"]+)')

@register.filter(name='md2html')
def md2html(txt, stripP=False):
    'converst ReST to HTML using pandoc, w/ audio support'
    txt, markers = add_temporary_markers(txt, find_audio)
    txt = pypandoc.convert(txt, 'html', format='rst',
                           extra_args=('--mathjax',))
    txt = replace_temporary_markers(txt, audio_html, markers)
    txt = StaticImagePat.sub(staticfiles.static('ct/') + r'\1', txt)
    if stripP and txt.startswith('<p>') and txt.endswith('</p>'):
        txt = txt[3:-4]
    return mark_safe(txt)

def nolongerused():
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

def find_audio(txt, lastpos, tag='.. audio::'):
        i = txt.find(tag, lastpos)
        if i < 0:
            return -1, None, None
        lastpos = i + len(tag)
        k = txt.find('\n', lastpos)
        if k < 0:
            return -1, None, None
        v = txt[lastpos:k].strip()
        return i, k, v

def audio_html(filename):
    i = filename.rfind('.')
    if i > 0: # remove file suffix
        filename = filename[:i]
    return '<audio controls><source src="STATICIMAGE/%s.ogg" type="audio/ogg"><source src="STATICIMAGE/%s.mp3" type="audio/mpeg">no support for audio!</audio>' \
      % (filename,filename)
    
def add_temporary_markers(txt, func, l=None):
    s = ''
    lastpos = 0
    if l is None:
        l = []
    while True: # replace selected content with unique markers
        i, j, v = func(txt, lastpos)
        if i < 0: # missing terminator, so treat as regular text
            break
        marker = 'mArKeR:%d:' % len(l)
        l.append((marker, v))
        s += marker
        lastpos = j
    s += txt[lastpos:]
    return s, l

def replace_temporary_markers(txt, func, l):
    s = ''
    lastpos = 0
    for marker, v in l: # put them back in after conversion
        i = txt.find(marker, lastpos)
        if i < 0:
            continue # must have been removed by comment, so ignore
        s += txt[lastpos:i] + func(v)  # substitute value
        lastpos = i + len(marker)
    s += txt[lastpos:]
    return s
