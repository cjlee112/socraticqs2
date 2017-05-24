import json

from django.utils import timezone
from django.db import models
from django.contrib.auth import login
from django.contrib.auth.models import User
from social.apps.django_app.default.models import UserSocialAuth

from ct.models import Role, Course
from .utils import (
    create_courselets_user, key_secret_generator, hash_lti_user_data
)


class LtiConsumer(models.Model):
    """
    Model to manage LTI consumers.
    """
    consumer_name = models.CharField(max_length=255, unique=True)
    consumer_key = models.CharField(max_length=64, unique=True, db_index=True, default=key_secret_generator)
    consumer_secret = models.CharField(max_length=64, unique=True, default=key_secret_generator)
    instance_guid = models.CharField(max_length=255, blank=True, null=True, unique=True)
    expiration_date = models.DateField(verbose_name='Consumer Key expiration date', null=True, blank=True)

    @staticmethod
    def get_or_combine(instance_guid, consumer_key):
        """
        Search for LtiConsumer instance by `instance_guid`.

        If there are no LtiConsumer found by `instance_guid`
        it will be searched by `consumer_key`.
        Also `instance_guid` will be added to found by `consumer_key`
        instance.
        """
        consumer = None
        if instance_guid:
            consumer = LtiConsumer.objects.filter(
                instance_guid=instance_guid
            ).first()

        if not consumer:
            consumer = LtiConsumer.objects.filter(
                consumer_key=consumer_key,
            ).first()

        if not consumer:
            return None

        if instance_guid and not consumer.instance_guid:
            consumer.instance_guid = instance_guid
            consumer.save()
        return consumer


class LTIUser(models.Model):
    """Model for LTI user

    **Fields:**

      .. attribute:: user_id
      uniquely identifies the user within LTI Consumer

      .. attribute:: consumer
      uniquely  identifies the Tool Consumer

      .. attribute:: extra_data
      user params received from LTI Consumer

      .. attribute:: django_user
      Django user to store study progress

      .. attribute:: context_id
      Context id given from LTI params

    LTI user params saved to extra_data field::

        'user_id'
        'context_id'
        'lis_person_name_full'
        'lis_person_name_given'
        'lis_person_name_family'
        'lis_person_sourcedid'
        'tool_consumer_instance_guid'
        'lis_person_contact_email_primary'
        'tool_consumer_info_product_family_code'
    """
    user_id = models.CharField(max_length=255, blank=False)
    consumer = models.CharField(max_length=64, blank=True)
    lti_consumer = models.ForeignKey(LtiConsumer, null=True)
    extra_data = models.TextField(max_length=1024, blank=False)
    django_user = models.ForeignKey(User, null=True, related_name='lti_auth')

    class Meta:  # pragma: no cover
        unique_together = ('user_id', 'lti_consumer')

    def create_links(self):
        """
        Create all needed links to Django and/or UserSocialAuth.
        """
        extra_data = json.loads(self.extra_data)

        first_name = extra_data.get('lis_person_name_given', '')
        last_name = extra_data.get('lis_person_name_family', '')
        email = extra_data.get('lis_person_contact_email_primary', '').lower()

        django_user = None

        defaults = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

        if email:
            social = UserSocialAuth.objects.filter(
                provider='email', uid=email
            ).first()

            if social:
                django_user = social.user
            else:
                django_user = User.objects.filter(email=email).first()

        if not django_user:
            username = hash_lti_user_data(
                self.user_id,
                extra_data.get('tool_consumer_instance_guid', ''),
                extra_data.get('lis_person_sourcedid', '')
            )
            django_user, _ = User.objects.get_or_create(
                username=username, defaults=defaults
            )
            if email:
                social = UserSocialAuth(
                    user=django_user,
                    provider='email',
                    uid=email,
                    extra_data=extra_data
                )
                social.save()

        self.django_user = django_user
        self.save()

    def login(self, request):
        """
        Login linked Django user.
        """
        if self.django_user:
            self.django_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, self.django_user)

    def enroll(self, roles, course_id):
        """Create Role according to user roles from LTI POST

        roles -> roles of LTI user given from LTI Consumer
        course_id -> Course entry id given from Launch URL

        :param roles: (str|list)
        :param course_id: int
        :return: None
        """
        if not isinstance(roles, list):
            roles = roles.split(',')
        course = Course.objects.filter(id=course_id).first()
        if course:
            for role in roles:
                kwargs = dict(
                    role=role,
                    course=course,
                    user=self.django_user
                )
                role = Role.objects.filter(**kwargs).first()
                if not role:
                    Role.objects.create(**kwargs)

    def is_enrolled(self, roles, course_id):
        """Check enroll status

        :param roles: (str|list)
        :param course_id: int
        :return: bool
        """
        if not isinstance(roles, list):
            roles = roles.split(',')
        course = Course.objects.filter(id=course_id).first()
        if Role.INSTRUCTOR in roles:
            role = Role.INSTRUCTOR
        else:
            role = Role.ENROLLED
        if course:
            return Role.objects.filter(
                role=role,
                course=course,
                user=self.django_user
            ).exists()

    @property
    def is_linked(self):
        """Check link to some Django user

        :return: bool
        """
        return bool(self.django_user)


class CourseRef(models.Model):  # pragma: no cover
    """Course reference

    Represent Course reference with meta information
    such as::

        course -> Courslet Course entry
        instructors -> list of User entry
        date - > creation date
        context_id -> LTI context_id
        tc_guid - > LTI tool_consumer_instance_guid
    """
    course = models.ForeignKey(Course, verbose_name='Courslet Course')
    instructors = models.ManyToManyField(User, verbose_name='Course Instructors')
    date = models.DateTimeField('Creation date and time', default=timezone.now)
    context_id = models.CharField('LTI context_id', max_length=254)
    tc_guid = models.CharField('LTI tool_consumer_instance_guid', max_length=128)

    class Meta:
        verbose_name = "CourseRef"
        verbose_name_plural = "CourseRefs"
        unique_together = ('context_id', 'course')

    def __str__(self):
        return '{0} {1}'.format(
            self.course.title, str(self.date.strftime('%H:%M %d-%m-%y'))
        )


class OutcomeService(models.Model):
    lis_outcome_service_url = models.CharField(max_length=255, unique=True)
    # lti_consumer = models.ForeignKey(LtiConsumer)

    def __unicode__(self):
        return self.lis_outcome_service_url


class GradedLaunch(models.Model):
    user = models.ForeignKey(User, db_index=True)
    course_id = models.IntegerField(db_index=True)
    outcome_service = models.ForeignKey(OutcomeService)
    lis_result_sourcedid = models.CharField(max_length=255, db_index=True)

    class Meta(object):
        unique_together = ('outcome_service', 'lis_result_sourcedid')

    def __unicode__(self):
        return self.lis_result_sourcedid
