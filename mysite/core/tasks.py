import logging

from intercom.client import Client
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from celery import shared_task


log = logging.getLogger(__name__)
intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)


@shared_task
def intercom_event(event_name, created_at, email, metadata):    
    intercom.events.create(
        event_name=event_name,
        created_at=created_at,
        email=email,
        metadata=metadata
    )
    log.info("{}:{}:{}:{}".format(event_name, created_at, email, metadata))


@shared_task
def faq_notify_instructors(**kwargs):
    if kwargs.get('instructors') and kwargs.get('faq_link'):
        subj_template = loader.get_template('ct/email/faq_notify_subject')
        rendered_subj = subj_template.render(kwargs)

        text_template = loader.get_template('ct/email/faq_notify_text')
        rendered_text = text_template.render(kwargs)

        send_mail(
            rendered_subj,
            rendered_text,
            settings.EMAIL_FROM,
            kwargs.get('instructors'),
            fail_silently=False,
        )


@shared_task
def faq_notify_students(**kwargs):
    if kwargs.get('students') and kwargs.get('faq_link'):
        subj_template = loader.get_template('ct/email/faq_notify_students_subject')
        rendered_subj = subj_template.render(kwargs)

        text_template = loader.get_template('ct/email/faq_notify_students_text')
        rendered_text = text_template.render(kwargs)

        send_mail(
            rendered_subj,
            rendered_text,
            settings.EMAIL_FROM,
            kwargs.get('students'),
            fail_silently=False,
        )
