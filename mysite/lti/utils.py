from django.http import HttpResponse


def only_lti(fn):
    def wrapped(request, *args, **kwargs):
        try:
            request.session['LTI_POST']
        except KeyError:
            return HttpResponse(content=b'Only LTI allowed')
        else:
            return fn(request, *args, **kwargs)
    return wrapped
