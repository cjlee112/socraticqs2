from functools import wraps
import string
import random
import uuid

from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User


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
    """
    password = str(uuid.uuid4())

    created = False
    while not created:
        try:
            username = generate_random_courselets_username()
            with transaction.atomic():
                courselets_user = User.objects.create_user(
                    username=username,
                    password=password,
                )
            created = True
        except IntegrityError:
            pass

    return courselets_user


def generate_random_courselets_username():
    """
    Create a valid random Courselets username.
    """
    allowable_chars = string.ascii_letters + string.digits
    username = ''
    for _index in range(30):
        username = username + random.SystemRandom().choice(allowable_chars)
    return username
