"""
Various utilities.
"""
import functools

from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader, Context

from core.common.mongo import c_onboarding_status, c_onboarding_settings
from core.common import onboarding


def send_email(context_data, from_email, to_email, template_subject, template_text):
    """
    Send an email with specified content.

    Arguments:
        context_data (dict): data to be passed to templates.
        from_email (str): sender's email.
        to_email (list): list of addresses to send an email to.
        template_subject (str): path to a subject template, e.g. 'ctms/email/subject.txt'
        template_text (str):  path to a body template, e.g. 'ctms/email/text.txt'
    """
    context = Context(context_data)

    subj_template = loader.get_template(template_subject)
    rendered_subj = subj_template.render(context)

    text_template = loader.get_template(template_text)
    rendered_text = text_template.render(context)

    send_mail(
        rendered_subj,
        rendered_text,
        from_email,
        to_email,
        fail_silently=True
    )


def suspending_receiver(signal, **decorator_kwargs):
    """
    Custom decorator to disable signals.

    Reference:
        https://devblog.kogan.com/blog/disable-signal-receivers-in-your-django-tests
    """
    def our_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            if settings.SUSPEND_SIGNALS:
                return
            return func(sender, **kwargs)
        return fake_receiver
    return our_wrapper


def get_onboarding_steps():
    """
    Get fields from somewhere, haven't decided yet

    Return list of steps to be done
    """
    return [
        onboarding.STEP_1,
        onboarding.STEP_2,
        onboarding.STEP_3,
        onboarding.STEP_4,
        onboarding.STEP_5,
        onboarding.STEP_6,
        onboarding.STEP_7
    ]


def get_onboarding_percentage(user_id):
    if user_id:
        status = c_onboarding_status(use_secondary=True).find_one({onboarding.USER_ID: user_id}) or {}
        if status:
            steps = [status.get(key, False) for key in get_onboarding_steps()]
            return round(
                len(filter(lambda x: x, steps)) / float(len(steps)) * 100,
                0
            )
    return 0


def update_onboarding_step(step, user_id):
    find_crit = {onboarding.USER_ID: user_id}
    onboarding_data = c_onboarding_status(use_secondary=True).find_one(find_crit)
    if not onboarding_data or not onboarding_data.get(step):
        c_onboarding_status().update_one(find_crit, {'$set': {
            step: True
        }}, upsert=True)


ONBOARDING_SETTINGS_DEFAULT = {
    onboarding.INTRODUCTION_COURSE_ID: settings.ONBOARDING_INTRODUCTION_COURSE_ID
}


def get_onboarding_setting(setting_name):
    setting_value = ONBOARDING_SETTINGS_DEFAULT.get(setting_name)
    onboarding_setting = [_ for _ in c_onboarding_settings().find().sort('_id', -1).limit(1)]
    onboarding_setting = onboarding_setting[0] if onboarding_setting else {}
    if onboarding_setting and onboarding_setting.get(setting_name):
        setting_value = onboarding_setting.get(setting_name)
    return setting_value
