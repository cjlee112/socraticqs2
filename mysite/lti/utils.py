import hashlib
from uuid import uuid4
from functools import wraps

from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.conf import settings


def only_lti(fn):
    """
    Decorator ensures that user comes from LTI session.
    """
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        try:
            request.session['LTI_POST']
        except KeyError:
            return HttpResponse(content=b'Only LTI allowed')
        else:
            return fn(request, *args, **kwargs)
    return wrapped


def create_courselets_user():
    """Creates Courselets user w/ random username.

    We can't trust LTI request w/o email in details.
    Using random username we need to check for
    IntegrityError DB exception to avoid race condition.
    """
    password = str(uuid4())

    created = False
    while not created:
        try:
            username = uuid4().hex[:30]
            with transaction.atomic():
                courselets_user = User.objects.create_user(
                    username=username,
                    password=password,
                )
            created = True
        except IntegrityError:
            pass

    return courselets_user


def key_secret_generator():
    """
    Generate a key/secret for LtiConsumer.
    """
    hash = hashlib.sha1(bytes(uuid4().hex, 'latin-1'))
    hash.update(bytes(settings.SECRET_KEY, 'latin-1'))
    return hash.hexdigest()[::2]


def hash_lti_user_data(user_id, tool_consumer_instance_guid, lis_person_sourcedid):
    """
    Create unique ID for Django user based on TC user.
    """
    h = hashlib.new('ripemd160')
    h.update(user_id.encode('utf-8'))
    h.update(tool_consumer_instance_guid.encode('utf-8'))
    h.update(lis_person_sourcedid.encode('utf-8'))

    # Return 30 chars Django 1.8
    return h.hexdigest()[:30]
