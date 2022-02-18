import re
import os
import time
from uuid import uuid4

from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.http.response import Http404
from django.template import loader
from django.utils.safestring import mark_safe
from django.contrib.postgres.fields import JSONField

from accounts.models import Instructor, search_user_by_email, clean_email_name
from chat.models import EnrollUnitCode
from core.common.utils import create_onboarding_event
from ct.models import Course


STATUS_CHOICES = (
    ('pending', 'pending'),
    ('joined', 'joined'),
)

TYPE_CHOICES = (
    ('student', 'student'),
    ('tester', 'tester'),
    ('professor', 'professor'),
    ('blindspotter', 'blindspotter'),
    ('teacher', 'teacher'),
    ('parent', 'parent'),
    ('blank', 'blank')
)

class InviteReplayError(ValueError):
    pass


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
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    email = models.EmailField()
    code = models.CharField('invite code', max_length=255)
    status = models.CharField('status', max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField('invite type', max_length=50, choices=TYPE_CHOICES, default='tester')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enroll_unit_code = models.ForeignKey(EnrollUnitCode, null=True, on_delete=models.CASCADE)
    data = JSONField(null=True, blank=True)  # JSON DATA

    added = models.DateTimeField('added datetime', auto_now_add=True)

    objects = InviteQuerySet.as_manager()

    @classmethod
    def create_new(cls, commit, course, instructor, email, invite_type, enroll_unit_code,
                   data=None):
        user = search_user_by_email(email)
        code = Invite(
            instructor=instructor,
            user=user,
            email=email,
            code=uuid4().hex,
            status='pending',
            type=invite_type,
            course=course,
            enroll_unit_code=enroll_unit_code,
            data=data
        )
        if commit:
            code.save()
        return code

    def get_invited_user_username(self):
        return self.email.split("@")[0] if self.email else ''

    class Meta:
        unique_together = ('instructor', 'email', 'type', 'course', 'enroll_unit_code')

    def render_template(self, request, messageType, part='text', **kwargs):
        context = {
            'invite': self,
            'current_site': Site.objects.get_current(request),
            'requestor': request.user
        }
        context.update(kwargs)
        text_template = loader.get_template(f'ctms/email/invite/{messageType}_{part}.txt')
        return text_template.render(context)

    def send_mail(self, request, messageType=None, **kwargs):
        'send the specified invite email message type'
        if not messageType:
            messageType = self.type
        rendered_subj = self.render_template(request, messageType, 'subject', **kwargs).strip()
        rendered_text = self.render_template(request, messageType, 'text', **kwargs)
        if 'senderName' in kwargs:
            email_from = f'{kwargs["senderName"]} <{settings.EMAIL_FROM}>' # RFC822 format
        else:
            email_from = settings.EMAIL_FROM
        send_mail(rendered_subj, rendered_text, email_from, [self.email], fail_silently=False)
        create_onboarding_event(
                event_name='invitation-sent',
                created_at=int(time.mktime(time.localtime())),
                email=self.instructor.user.email,
                metadata={'invitee': self.email}
        )
        return {
                'success': True,
                'message': 'Invitation successfully sent.',
                'invite': {
                    'status': self.status,
                }
        }

    def get_existing_user(self):
        'look for user with same email address'
        if self.user:
            return self.user
        else:
            return search_user_by_email(self.email)

    def create_unique_user(self, password, first_name, last_name, is_active=False,
                           minlength=4, maxtry=1000):
        'find a unique username and create new django User'
        username = self.get_invited_user_username()
        if len(username) < minlength:
            username = first_name + '_' + last_name
        userbase = username
        i = 0
        while i < maxtry: # no infinite loops, please
            try:
                user = User.objects.create_user(username, self.email, password)
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = is_active
                user.save()
                self.user = user
                self.save()
                return user
            except IntegrityError: # extend name to be unique
                i += 1
                username = userbase + str(i) # just append a number
        raise ValueError(f'Exceeded Invite.create_unique_user() maxtry: {userbase}, {i}')

    def finish_acceptance(self):
        'finalize Invite, User, Role records as needed for user to start the invited work'
        self.user.is_active = True
        self.user.save()
        self.status = 'joined'
        self.save()
        # TODO: do we need to create Role for enrolling in course?

    def login_accepted_invite(self, request):
        'login accepted invite (based on Invite code, not password)'
        if self.status != 'pending':
            raise InviteReplayError('This invitation has already been used.  Please use the usual login page.')
        if self.user == request.user: # already logged in, so just update Invite record
            self.finish_acceptance()
            return
        elif request.user.is_authenticated: # session logged into another account??
            # TODO: we should handle this by offering to merge the two accounts 
            logout(request) # logout existing session prior to logging in invited user
        self.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, self.user)
        self.finish_acceptance()

    def get_absolute_url(self):
        return reverse('ctms:tester_join_course', kwargs={'code': self.code})

    # TODO: refactor it ASAP, it may result in errors in certain cases
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

    def __str__(self):
        return f'Code {self.code}, User {self.email}'


class BestPracticeTemplate(models.Model):
    """
    Model for types of Best Practices for course or courselet scope.
    """
    COURSE = 'course'
    COURSELET = 'courselet'
    BP_SCOPES = (
        (COURSE, 'Course'),
        (COURSELET, 'Courselet')
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, null=True)
    explanation = models.TextField(blank=True, null=True)
    metric = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    scope = models.CharField(max_length=10, choices=BP_SCOPES, db_index=True)
    calculation = JSONField(blank=True, null=True)
    config = JSONField(blank=True, null=True)
    activation = JSONField(blank=True, null=True)
    summary = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f'{self.title} scope: {self.scope}'


class BestPractice(models.Model):
    """
    Model for instances where a BP could be implemented in a course/courselet.
    """
    CONVERTED_STATUS = (
        ('pending', 'it will be converted shortly'),
        ('done', 'it has been converted'),
    )

    template = models.ForeignKey('BestPracticeTemplate', null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey('ct.Course', null=True, blank=True, on_delete=models.CASCADE)
    courselet = models.ForeignKey('ct.CourseUnit', null=True, blank=True, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    data = JSONField(blank=True, null=True)
    upload_file = models.FileField(
        upload_to='practice_questions/', blank=True, null=True)
    converted_status = models.CharField('status', max_length=20, choices=CONVERTED_STATUS, default='pending')

    @property
    def filename(self):
        return os.path.basename(self.upload_file.name)

    def summary_fg(self) -> str:
        return mark_safe(f'''
            Practice exam divided into {self.courselet.unit.unitlesson_set.count()} threads
            <a href={
                reverse(
                    "ctms:courslet_view",
                    kwargs={"course_pk": self.courselet.course.id, "pk": self.courselet.id})
            }>(click here to View)</a>
        ''')

    # TODO do dynamic summary invocation throught descriptor (probably)
    @property
    def summary(self) -> str:
        summary_engine = getattr(self, self.template.summary) if self.template.summary else None
        return summary_engine() if self.template.summary else ''

    def __str__(self) -> str:
        return self.template.title


class BestPractice1(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    student_count = models.IntegerField('How many students do you have in your class?')
    misconceptions_count = models.IntegerField(
        'How many individual student misconceptions in your class did you fix today'' (or your average teaching day)?'
    )
    question_count = models.IntegerField(
        'Number of question-parts in your typical exam (e.g. 8 questions with 3 parts each = 24)?'
    )
    mean_percent = models.IntegerField('Mean percent score on this exam?')
    activate = models.BooleanField(blank=True)
    estimated_blindspots = models.IntegerField(blank=True)
    estimated_blindspots_courselets = models.IntegerField(blank=True)
    pdf = models.FileField(
        upload_to='best_practices/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'jpg'])]
    )

    def __str__(self) -> str:
        return f'{self.__class__.__name__} for user {self.user}'


class BestPractice2(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    percent_engaged = models.IntegerField(
        'What percent of students are fully engaged, '
        'i.e. would immediately do any optional exercises you provide, just to '
        'improve their understanding?'
    )
    activate = models.BooleanField(blank=True)
    estimated_blindspots = models.IntegerField(blank=True)
    estimated_blindspots_courselets = models.IntegerField(blank=True)

    def __str__(self) -> str:
        return f'{self.__class__.__name__} for user {self.user}'
