from intercom.client import Client
from django.conf import settings
from celery import shared_task


intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)


@shared_task
def intercom_event(event_name, created_at, email, metadata):
    intercom.events.create(
        event_name=event_name,
        created_at=created_at,
        email=email,
        metadata=metadata
    )
