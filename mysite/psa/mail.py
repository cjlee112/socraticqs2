"""
Module defined send_validation function to verify emails.
"""
from django.conf import settings
from django.template import loader
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.context import Context


def send_validation(strategy, backend, code):
    """
    Send email validation link.
    """
    # TODO add email validating regex [^@]+@[^@]+\.[^@]+
    url = (reverse('social:complete', args=(backend.name,)) +
           '?verification_code=' + code.code)
    url = strategy.request.build_absolute_uri(url)
    context = Context({
        'code': code,
        'url': url,
    })

    subj_template = loader.get_template('psa/email/confirmation_subject.txt')
    rendered_subj = subj_template.render(context)

    text_template = loader.get_template('psa/email/confirmation_text.txt')
    rendered_text = text_template.render(context)

    send_mail(
        rendered_subj,
        rendered_text,
        # 'Validate your account',
        # 'Validate your account {0}'.format(url),
        settings.EMAIL_FROM,
        [code.email],
        fail_silently=False
    )
