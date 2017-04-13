from uuid import uuid4
from django.db.utils import IntegrityError
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
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

    @classmethod
    def create_new(cls, commit, course, instructor, email, invite_type):
        user = User.objects.filter(email=email).first()
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

    class Meta:
        unique_together = ('instructor', 'email', 'type', 'course')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        user = User.objects.filter(email=self.email).first()
        if user:
            self.user = user
        return super(Invite, self).save(force_insert, force_update, using, update_fields)

    def send_mail(self, request, view):
        try:
            send_mail(
                "{} invited you in a course <{}> as {}".format(
                    self.instructor.user.get_full_name() or self.instructor.user.username,
                    self.course,
                    self.type
                ),
                '<a href="{}{}">Click to open</a>'.format(Site.objects.get_current(request),
                                                          reverse('ctms:tester_join_course',
                                                                  kwargs={'code': self.code})),

                settings.EMAIL_FROM,
                [self.email],
                fail_silently=True
            )
            return view.render(
                    'ctms/invite_link_sent.html',
                    {
                        'course': self.course,
                        'with_user': self.email
                    }
                )
        except IntegrityError:
            return view.render(
                'ctms/error.html',
                context={'message': 'You already have sent invite to user with {} email'.format(
                    request.POST['email'])
                },
            )
