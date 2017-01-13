from django.views.decorators.cache import cache_page
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import loader, RequestContext


cache_page(60*15)
def home_page(request):
    return render(request, 'index.html')


def logout_page(request, next_page):
    """
    Log users out and re-direct them to the main page.
    """
    logout(request)
    return HttpResponseRedirect(next_page)


def markup_view(request, path=''):
    """
    Views that allow to review markup during developing.
    """
    if path[-1] == '/':
        templatepath = path[:-1]
    else:
        templatepath = path
    template = loader.get_template('markup/' + templatepath)
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))
