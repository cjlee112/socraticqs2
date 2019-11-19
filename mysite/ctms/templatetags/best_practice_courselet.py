from django import template


register = template.Library()


@register.filter(name='active')
def active(obj, courselet):
    return obj.filter(active=True, course__isnull=True, courselet=courselet)


@register.filter(name='bps_exists')
def bps_exists(obj, courselet):
    return obj.filter(active=True, courselet=courselet).exists()
