"""
Email sending utils to generalize celery background tasks.
"""
import logging

from django.core.mail import BadHeaderError, send_mail


log = logging.getLogger(__name__)


def send_emails(subj: str, text: str, email_from: str, recipients: list, fail_silently=False) -> None:
    """
    Sending email sequentially.
    """
    for recipient in recipients:
        try:
            send_mail(subj, text, email_from, [recipient], fail_silently=fail_silently)
        except BadHeaderError as e:
            log.error(f'Invalid header found. {e}')
            continue
