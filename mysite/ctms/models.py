import re
from uuid import uuid4
from django.template import loader, Context
from django.db.utils import IntegrityError
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from accounts.models import Instructor

from ct.models import Course


STATUS_CHOICES = (
    ('pendind', 'pending'),
    ('joined', 'joined'),
)

TYPE_CHOICES = (
    ('student', 'student'),
    ('tester', 'tester')
)

def clean_email_name(email):
    email_name, domain = email.split('@', 1)
    email_name = email_name.replace('.', '')
    return email_name, domain

class InviteQuerySet(models.QuerySet):
    def my_invites(self, request):
        return self.filter(instructor=request.user.instructor)

    def testers(self):
        return self.filter(type='tester')

    def students(self):
        return self.filter(type='student')

    def shared_for_me(self, request):
        return self.filter(
            models.Q(user=request.user) | models.Q(email=request.user.email)
        )


class Invite(models.Model):
    instructor = models.ForeignKey(Instructor)
    user = models.ForeignKey(User, blank=True, null=True)
    email = models.EmailField()
    code = models.CharField('invite code', max_length=255)
    status = models.CharField('status', max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField('invite type', max_length=50, choices=TYPE_CHOICES, default='tester')
    course = models.ForeignKey(Course)

    added = models.DateTimeField('added datetime', auto_now_add=True)

    objects = InviteQuerySet.as_manager()

    @staticmethod
    def search_user_by_email(email):
        email_name, domain = clean_email_name(email)
        return User.objects.filter(
            models.Q(email=email) |
            models.Q(email__iregex="^{}@{}$".format(r"\.?".join(email_name), domain))
        ).first()

    @classmethod
    def create_new(cls, commit, course, instructor, email, invite_type):
        user = Invite.search_user_by_email(email)
        try:
            old_invite = Invite.get_by_user_or_404(
                user=user,
                type=invite_type,
                course=course,
                instructor=instructor
            )
            if old_invite:
                return old_invite
        except Http404:
            pass
        code = Invite(
            instructor=instructor,
            user=user,
            email=email,
            code=uuid4().hex,
            status='pending',
            type=invite_type,
            course=course,
        )
        if commit:
            code.save()
        return code

    def get_invited_user_username(self):
        return self.email.split("@")[0] if self.email else ''

    class Meta:
        unique_together = ('instructor', 'email', 'type', 'course')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        user = Invite.search_user_by_email(self.email)
        self.user = user
        return super(Invite, self).save(force_insert, force_update, using, update_fields)

    def send_mail(self, request, view):
        try:
            context = Context({
                'invite': self,
                'current_site': Site.objects.get_current(request)
            })
            subj_template = loader.get_template('ctms/email/invite_subject.txt')
            rendered_subj = subj_template.render(context)

            text_template = loader.get_template('ctms/email/invite_text.txt')
            rendered_text = text_template.render(context)

            send_mail(
                rendered_subj,
                rendered_text,
                settings.EMAIL_FROM,
                [self.email],
                fail_silently=True
            )
            return {
                'success': True,
                'message': 'Invitation successfully sent.',
                'invite': {
                    'status': self.status,
                }
            }
        except IntegrityError:
            return {
                'success': False,
                'message': 'You already have sent invite to user with {} email'.format(request.POST['email'])
            }

    def get_absolute_url(self):
        return reverse('ctms:tester_join_course', kwargs={'code': self.code})

    @staticmethod
    def get_by_user_or_404(user, **kwargs):
        '''
        Do a search for invite by passed parameters and user.
         NOTE: this function firstly try to get invite by passed kwargs,
         then check that Invite.email and user.email are equal,
         if they not - trying to check Invite.email and user.email
         !! excluding dots from email-name. !!
        :param user: request.user
        :param kwargs: params to search by
        :return: invite if found
        :raise: Http404 if not found
        '''
        if not user:
            raise Http404
        invites = Invite.objects.filter(
            **kwargs
        )
        my_invite = None

        for invite in invites:
            if invite and invite.email == user.email:
                my_invite = invite
                break
            user_email_name, user_domain = clean_email_name(user.email)
            invite_email, invite_domain = clean_email_name(invite.email)
            if invite_domain != user_domain:
                continue
            res = re.search(
                "^{}@{}$".format(r"\.?".join(user_email_name), user_domain),
                "{}@{}".format(invite_email, invite_domain)
            )
            if res and res.string:
                my_invite = invite
                break
        else:
            raise Http404()
        if my_invite:
            return my_invite
        else:
            raise Http404()

    def __unicode__(self):
        return "Code {}, User {}".format(self.code, self.email)
