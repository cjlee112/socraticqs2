from django.conf import settings


def debug_settings(request):

    return {
        'DEBUG': settings.DEBUG,
    }