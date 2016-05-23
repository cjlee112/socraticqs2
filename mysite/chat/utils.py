import hashlib
from uuid import uuid4

from django.conf import settings


def enroll_generator():
    """
    Generate a key/secret for LtiConsumer.
    """
    hash = hashlib.sha1(uuid4().hex)
    hash.update(settings.SECRET_KEY)
    return hash.hexdigest()[::2]
