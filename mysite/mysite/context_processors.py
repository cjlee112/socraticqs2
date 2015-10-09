from django.conf import settings


def google_analytics(request):
    """
    Add GOOGLE_ANALYTICS_CODE to context.
    """
    if hasattr(settings, 'GOOGLE_ANALYTICS_CODE'):
        return {'GOOGLE_ANALYTICS_CODE': settings.GOOGLE_ANALYTICS_CODE}
    return {}
