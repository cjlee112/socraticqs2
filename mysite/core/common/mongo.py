"""
Core MongoDB connector.
"""
import pymongo
from pymongo import ReadPreference

from django.conf import settings


DB_DATA = settings.DB_DATA

COLLECTION_CHAT_STACK = 'chat_stack'
COLLECTION_MILESTONE_ORCT = 'milestone_students_orct'
COLLECTION_ONBOARDING_STATUS = 'onboarding_status'
COLLECTION_ONBOARDING_SETTINGS = 'onboarding_settings'


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


class MongoConnector(Singleton):
    """
    Mongo connector as singleton object to utilize
    mongo connection pool.
    """
    _conn = None

    @property
    def connector(self):
        if not self._conn:
            self._mongo_init()
        return self._conn

    def _mongo_init(self):
        """
        Set class _conn variable.
        """
        self._conn = pymongo.MongoClient(settings.MONGO_HOST)


_conn = MongoConnector()


def mongo_data_database(db=DB_DATA, use_secondary=False):
    _read_preference = (
        ReadPreference.SECONDARY_PREFERRED
        if use_secondary else
        ReadPreference.PRIMARY
    )

    return _conn.connector.get_database(db, read_preference=_read_preference)


def c_chat_stack(use_secondary=False):
    return mongo_data_database(use_secondary=use_secondary)[COLLECTION_CHAT_STACK]


def c_milestone_orct(use_secondary=False):
    return mongo_data_database(use_secondary=use_secondary)[COLLECTION_MILESTONE_ORCT]


def c_onboarding_status(use_secondary=False):
    return mongo_data_database(use_secondary=use_secondary)[COLLECTION_ONBOARDING_STATUS]


def c_onboarding_settings(use_secondary=False):
    return mongo_data_database(use_secondary=use_secondary)[COLLECTION_ONBOARDING_SETTINGS]


def do_health(use_secondary=False):
    db = mongo_data_database(use_secondary=use_secondary)
    return db.command('ping'), db.command('serverStatus')
