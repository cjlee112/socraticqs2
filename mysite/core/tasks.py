import logging
from datetime import datetime
from pytz import UTC

from intercom.client import Client
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
# from django.contrib.auth.models import User
# from django.contrib.sessions.models import Session

from mysite import celery_app
# from psa.models import UserSession


log = logging.getLogger(__name__)
intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)
LOGGER = logging.getLogger('celery_warn')


@celery_app.task
def intercom_event(event_name, created_at, email, metadata):    
    intercom.events.create(
        event_name=event_name,
        created_at=created_at,
        email=email,
        metadata=metadata
    )
    log.info("{}:{}:{}:{}".format(event_name, created_at, email, metadata))


@celery_app.task
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


@celery_app.task
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


# @celery_app.task
# def check_anonymous():
#     """Delete anonymous users

#     Find end delete anonymous users with expired user_sessions
#     or withour session at all.
#     """
#     now = datetime.utcnow().replace(tzinfo=UTC)
#     user_sessions = UserSession.objects.filter(
#         user__groups__name='Temporary'
#     )

#     # zombie_users - temporary students without session
#     zombie_users = (user for user in
#                     User.objects.filter(groups__name='Temporary')
#                     if user.id not in
#                     (session.user.id for session in user_sessions))

#     for zombie in zombie_users:
#         zombie.delete()

#     for user_session in user_sessions:
#         try:
#             user_session.session
#         except Session.DoesNotExist as e:
#             LOGGER.info(e)
#             # Delete users in UserSession but without session
#             user_session.user.delete()
#         else:
#             if user_session.session.expire_date < now:
#                 user_session.session.delete()
#                 user_session.user.delete()
