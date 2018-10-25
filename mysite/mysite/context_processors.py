from django.conf import settings
from core.common.mongo import c_onboarding_status
from core.common.utils import get_onboarding_percentage


def google_analytics(request):
    """
    Add GOOGLE_ANALYTICS_CODE to context.
    """
    if hasattr(settings, 'GOOGLE_ANALYTICS_CODE'):
        return {'GOOGLE_ANALYTICS_CODE': settings.GOOGLE_ANALYTICS_CODE}
    return {}


def onboarding_percentage_of_done(request):
    if request and request.user:
        return {
            'onboarding_percentage_of_done': get_onboarding_percentage(request.user.id)
        }
    return 0
