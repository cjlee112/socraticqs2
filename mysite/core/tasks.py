import logging

from intercom.client import Client
from django.conf import settings
from django.template import loader

from .utils import send_emails
from mysite import celery_app


log = logging.getLogger(__name__)
intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)
LOGGER = logging.getLogger('celery_warn')


@celery_app.task
def intercom_event(event_name, created_at, email, metadata) -> None:
    intercom.events.create(
        event_name=event_name,
        created_at=created_at,
        email=email,
        metadata=metadata
    )
    log.info("{}:{}:{}:{}".format(event_name, created_at, email, metadata))


@celery_app.task
def faq_notify_instructors(**kwargs) -> None:
    if kwargs.get('instructors') and kwargs.get('faq_link'):
        subj_template = loader.get_template('ct/email/faq_notify_subject')
        rendered_subj = subj_template.render(kwargs)

        text_template = loader.get_template('ct/email/faq_notify_text')
        rendered_text = text_template.render(kwargs)

        send_emails(
            rendered_subj,
            rendered_text,
            settings.EMAIL_FROM,
            kwargs.get('instructors'),
        )


@celery_app.task
def faq_notify_students(**kwargs) -> None:
    if kwargs.get('students') and kwargs.get('faq_link'):
        subj_template = loader.get_template('ct/email/faq_notify_students_subject')
        rendered_subj = subj_template.render(kwargs)

        text_template = loader.get_template('ct/email/faq_notify_students_text')
        rendered_text = text_template.render(kwargs)

        send_emails(
            rendered_subj,
            rendered_text,
            settings.EMAIL_FROM,
            kwargs.get('students'),
        )
