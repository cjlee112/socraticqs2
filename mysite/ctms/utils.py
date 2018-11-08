"""
Misc utils for ctms application.
"""
from __future__ import unicode_literals

import hashlib

from django.utils.encoding import force_bytes


class Memoize(object):
    """
    Memoization/caching utility class.
    """
    def __init__(self, cache_prefix='memoize'):
        self.cache_prefix = cache_prefix

    def cache_key(self, fname, *args):
        """
        Returns a cache key for a given func_name and args.
        """
        cache_key = hashlib.md5(
            force_bytes((fname, args))
        ).hexdigest()
        return '%s:%s' % (self.cache_prefix, cache_key)
