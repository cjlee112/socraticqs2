from django.template import Context, loader
from django.core.mail import EmailMessage

from models import InterestedPlugin


def form_send(interested_form):
    """
    Send interested form
    """
    tmp = loader.get_template('pages/mail/interested_mail.html')
    cntx = Context({'form': interested_form})
    mail_body = tmp.render(cntx)
    email_to = InterestedPlugin.objects.first().email_to
    email = EmailMessage('Answer to Interested Form', mail_body, to=[email_to])
    email.send()
