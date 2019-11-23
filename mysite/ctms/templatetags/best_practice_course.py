from django import template


register = template.Library()


@register.filter(name='active')
def active(obj, course):
    return obj.filter(active=True, course=course, courselet__isnull=False)


@register.filter(name='bps_exists')
def bps_exists(obj, course):
    return obj.filter(active=True, course=course).exists()
