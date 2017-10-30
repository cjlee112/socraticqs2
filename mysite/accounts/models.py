from django.db.models.signals import post_save
import pygeoip

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Profile(models.Model):
    """
    This class represents user profile to store additional data, needed in application.
    Provides following fields:
     - `user` - one to one rel to User model
     - `timezone` - offset from UTC-0
    """
    user = models.OneToOneField(User)
    timezone = models.CharField(max_length=255, blank=True, null=True)

    @staticmethod
    def get_user_ip(request):
        """
        Return user IP from request.
        :param request: django request
        :return: IP
        """
        http_x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if http_x_forwarded_for:
            ip = http_x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


    @classmethod
    def check_tz(cls, request):
        """
        Check if self.timezone is empty - get timezone from pygeoip and store it there.
        :param request: django request
        :return: nothing
        """
        try:
            profile = request.user.profile
        except cls.DoesNotExist:
            profile = cls.objects.create(user=request.user)

        if profile.timezone not in pytz.all_timezones:
            gi = pygeoip.GeoIP(settings.GEO_IP_DB_PATH)
            loc_data = gi.record_by_addr(cls.get_user_ip(request)) or {}
            timezone = loc_data.get('time_zone', settings.TIME_ZONE)
            profile.timezone = timezone
            profile.save()


class Instructor(models.Model):
    """
    Profile model for Instructors.

    Provide following additionsl fields:
        - `Institution`
        - `Department`
        - `Job`
        - `icon_url`
        - `page_url`
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job = models.CharField(max_length=100, blank=True)
    icon_url = models.URLField(blank=True)
    page_url = models.URLField(blank=True)


def create_user_profile(sender, instance, created, **kwargs):
    """
    This function is a signal handler for User creation event, it creates user profile for new users.
    When hawe user has been create this function will be called with instance=new_user and create=True.
    """
    if created:
        Profile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User, dispatch_uid='create_user_profile')