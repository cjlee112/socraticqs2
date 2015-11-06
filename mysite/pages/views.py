from django.http import HttpResponse

from forms import InterestedModelForm
from tasks import form_send


def interested_form(request):
    obj = InterestedModelForm(request.POST)
    if obj.is_valid():
        obj.save()
        form_send(obj.clean())
        return HttpResponse("ok")
    else:
        return HttpResponse("fail", status=400)
