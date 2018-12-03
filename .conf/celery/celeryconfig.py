import os


BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379')
