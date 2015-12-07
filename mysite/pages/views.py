from django.http import JsonResponse

from pages.forms import InterestedModelForm
from pages.tasks import form_send


def interested_form(request):
    obj = InterestedModelForm(request.POST)
    if obj.is_valid():
        obj.save()
        form_send(obj.clean())
        return JsonResponse({'success': 'Thanks for contacting us! We will get in touch with you shortly.'})
    else:
        return JsonResponse({'error': 'Something went wrong. Please try again later.'})
