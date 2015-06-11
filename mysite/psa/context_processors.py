from django.conf import settings


def debug_settings(request):
    """
    Add DEBUG attr to context.
    """
    return {
        'DEBUG': settings.DEBUG,
    }
