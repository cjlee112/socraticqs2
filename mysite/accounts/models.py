from django.db.models.signals import post_save
import pygeoip
import pytz
import hashlib

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.contrib.postgres.fields import JSONField
from django.conf import settings
import pytz

ALL_TIMEZONES_CHOICES = [
    (i, i) for i in pytz.all_timezones
]


class Profile(models.Model):
    """
    This class represents user profile to store additional data, needed in application.
    Provides following fields:
     - `user` - one to one rel to User model
     - `timezone` - offset from UTC-0
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=255, blank=True, null=True, choices=ALL_TIMEZONES_CHOICES)
    data = JSONField(null=True, blank=True)  # JSON DATA

    @classmethod
    def get_for_user(cls, user):
        'return Profile object associated with user (create if missing)'
        try:
            return user.profile
        except cls.DoesNotExist:
            return cls.objects.create(user=user)


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
        :return: Profile object associated with request.user
        """
        profile = cls.get_for_user(request.user)
        if profile.timezone not in pytz.all_timezones:
            gi = pygeoip.GeoIP(settings.GEO_IP_DB_PATH)
            loc_data = gi.record_by_addr(cls.get_user_ip(request)) or {}
            timezone = loc_data.get('time_zone', settings.TIME_ZONE)
            profile.timezone = timezone
            profile.save()
        return profile

    def is_provisional(self):
        'True iff this is a provisional user account'
        return self.user.email.endswith(NO_EMAIL_VISITOR_DOMAIN) or not self.data or not 'email' in self.data.get('validations', {})

    def save_validation(self, validationPath, validationData):
        'set self.data["validations"][validationPath[0]][validationPath[1]]... = validationData'
        data = d = self.data or {}
        for k in ('validations',) + tuple(validationPath[:-1]): # follow path inside JSONField
            d = d.setdefault(k, {})
        d[validationPath[-1]] = validationData
        self.data = data
        self.save()
        
        


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
    what_do_you_teach = models.CharField(max_length=100, blank=True)
    data = JSONField(null=True, blank=True)  # JSON DATA

    def __str__(self):
        return self.user.username if not (self.user.last_name or self.user.first_name) else self.user.get_full_name()


def create_user_profile(sender, instance, created, **kwargs):
    """
    This function is a signal handler for User creation event, it creates user profile for new users.
    When hawe user has been create this function will be called with instance=new_user and create=True.
    """
    if created:
        Profile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User, dispatch_uid='create_user_profile')


def search_user_by_email(email):
    'return one User with matching email, or None if not found'
    return User.objects.filter(email=email).first()


def clean_email_name(email):
    'split email address into username (stripped of .) and domain'
    email_name, domain = email.split('@', 1)
    email_name = email_name.replace('.', '')
    return email_name, domain

def create_user_account(username, email, password, first_name, last_name, is_active=False):
    'create new account and return user object'
    user = User.objects.create_user(username, email, password)
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = is_active
    user.save()
    return user

def create_unique_user(email, password, first_name, last_name, username='', is_active=False,
                       minlength=4, maxtry=1000):
    'find a unique username and create new django User'
    if len(username) < minlength:
        username = first_name + '_' + last_name
    userbase = username
    i = 0
    while i < maxtry: # no infinite loops, please
        try:
            return create_user_account(username, email, password, first_name, last_name, is_active)
        except IntegrityError: # extend name to be unique
            i += 1
            username = userbase + str(i) # just append a number
    raise ValueError(f'Exceeded create_unique_user() maxtry: {userbase}, {i}')


def create_user_by_ip(ip, email, password, first_name, last_name, is_active=False):
    'create user account specific to this IP address'
    username = hashlib.sha256(ip).hexdigest()
    try:
        user = User.objects.get(username=username)
        return None # visitor account already associated with this IP address, refuse to create another
    except User.DoesNotExist:
        return create_user_account(username, email, password, first_name, last_name, is_active)



def login_this_session(request, user):
    'login the specified user in association with the current session'
    if request.user.is_authenticated: # session logged into another account??
        # TODO: we should handle this by offering to merge the two accounts 
        logout(request) # logout existing session prior to logging in specified user account
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

NO_EMAIL_VISITOR_DOMAIN = 'nonexistent.fun'


