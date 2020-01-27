from urllib.parse import urljoin

from django.conf import settings
from django.template import loader
from django.contrib.sites.models import Site
from django.urls import reverse

from core.utils import send_emails
from mysite import celery_app
from ct.models import Course


@celery_app.task
def notify_for_updates(**kwargs):
    """
    Notify students about new updates.
    """
    domain = 'https://{0}'.format(Site.objects.get_current().domain)
    for course in Course.objects.all():
        for courselet in course.get_course_units():
            for student in course.students:
                last_chat = student.chat_set.filter(enroll_code__courseUnit=courselet).order_by('id').last()
                if last_chat.is_history and last_chat.has_updates:
                    url = reverse(
                        'chat:chat_enroll',
                        kwargs={'enroll_key': last_chat.enroll_code.enrollCode}
                    )
                    kwargs = {
                        'student_first_name': student.first_name,
                        'instructor_full_name': last_chat.instructor.get_full_name,
                        'courselet_name': courselet,
                        'link_to_courselet': urljoin(domain, url + settings.UPDATES_HASH)
                    }
                    subj_template = loader.get_template('chat/email/notify_students_subject')
                    rendered_subj = subj_template.render(kwargs)

                    text_template = loader.get_template('chat/email/notify_students_text')
                    rendered_text = text_template.render(kwargs)

                    send_emails(rendered_subj, rendered_text, settings.EMAIL_FROM, [student.email])
