from __future__ import absolute_import

import os
import subprocess

import json
import requests
from django.core.management import call_command

from celery import Celery

from django.conf import settings


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

from pytz import UTC
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from psa.models import UserSession


@app.task
def check_anonymous():
    """Delete anonymous users

    Find end delete anonymous users with expired user_sessions
    or withour session at all.
    """
    now = datetime.utcnow().replace(tzinfo=UTC)
    user_sessions = UserSession.objects.filter(
        user__username__startswith='anonymous')

    # zombie_users - temporary students without session
    zombie_users = (user for user in
                    User.objects.filter(username__startswith='anonymous')
                    if user.id not in
                    (session.user.id for session in user_sessions))

    for zombie in zombie_users:
        zombie.delete()

    for user_session in user_sessions:
        try:
            user_session.session
        except Session.DoesNotExist as e:
            print(e)
            # Delete users in UserSession but without session
            user_session.user.delete()
        else:
            if user_session.session.expire_date < now:
                user_session.session.delete()
                user_session.user.delete()
