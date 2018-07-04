from uuid import uuid4


def enroll_generator():
    """
    Generate a random key
    """
    return uuid4().hex
