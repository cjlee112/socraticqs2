"""
Module defined send_validation function to verify emails.
"""
from django.conf import settings
from django.template import loader
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.context import Context


def send_validation(strategy, backend, code, *args, **kwargs):
    """
    Send email validation link.
    When user clicks <resened email> button on /ctms/email-sent/ page
    it will get CustomCode object from DB and populate request.POST with data from code object.
    """
    # TODO add email validating regex [^@]+@[^@]+\.[^@]+
    url = (reverse('social:complete', args=(backend.name,)) +
           '?verification_code=' + code.code)
    user_fields = (
        'first_name',
        'last_name',
        'institution',
        'email',
    )
    user_data = {f: strategy.request.POST.get(f, '') for f in user_fields}
    url = strategy.request.build_absolute_uri(url)
    context = Context({
        'code': code,
        'url': url,
        'user_data': user_data
    })

    subj_template = loader.get_template('psa/email/confirmation_subject.txt')
    rendered_subj = subj_template.render(context)

    text_template = loader.get_template('psa/email/confirmation_text.txt')
    rendered_text = text_template.render(context)
    send_mail(
        rendered_subj,
        rendered_text,
        settings.EMAIL_FROM,
        [code.email],
        fail_silently=False
    )
