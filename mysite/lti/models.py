import json
from django.db import models
from django.contrib.auth import login
from django.contrib.auth.models import User

from social.apps.django_app.default.models import UserSocialAuth

from ct.models import Role, Course


class LTIUser(models.Model):
    """Model for LTI user

    Fields:
    user_id -> uniquely identifies the user within LTI Consumer
    consumer -> uniquely  identifies the Tool Consumer
    extra_data -> user params received from LTI Consumer

    LTI user params saved to extra_data field:
        'user_id'
        'ext_lms'
        'lis_person_name_full'
        'lis_person_name_given'
        'lis_person_name_family'
        'lis_person_contact_email_primary'

    django_user -> Django user to store study progress
    course_id -> Course entry id given from Launch URL
    """
    user_id = models.CharField(max_length=255, blank=False)
    consumer = models.CharField(max_length=64, blank=True)
    extra_data = models.TextField(max_length=1024, blank=False)
    django_user = models.ForeignKey(User, null=True, related_name='lti_auth')
    course_id = models.IntegerField()

    class Meta:
        unique_together = ('user_id', 'consumer', 'course_id')

    def create_links(self):
        """Create all needed links to Django and/or UserSocialAuth"""
        extra_data = json.loads(self.extra_data)
        username = extra_data.get('lis_person_name_full', self.user_id)
        first_name = extra_data.get('lis_person_name_given', '')
        last_name = extra_data.get('lis_person_name_family', '')
        email = extra_data.get('lis_person_contact_email_primary', '').lower()

        defaults = {
            'first_name': first_name,
            'last_name': last_name,
        }

        if email:
            defaults['email'] = email
            social = UserSocialAuth.objects.filter(provider='email',
                                                   uid=email).first()
            if social:
                django_user = social.user
            else:
                django_user = User.objects.filter(email=email).first()
                if not django_user:
                    django_user, created = User.objects.get_or_create(
                        username=username, defaults=defaults
                    )
                social = UserSocialAuth(user=django_user,
                                        provider='email',
                                        uid=email,
                                        extra_data=extra_data)
                social.save()
        else:
            django_user, created = User.objects.get_or_create(username=username,
                                                              defaults=defaults)
        self.django_user = django_user
        self.save()

    def login(self, request):
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
                Role.objects.get_or_create(course=course,
                                           user=self.django_user,
                                           role=role)

    def is_enrolled(self, roles, course_id):
        """Check enroll status

        :param roles: (str|list)
        :param course_id: int
        :return: ct.Role
        """
        if not isinstance(roles, list):
            roles = roles.split(',')
        course = Course.objects.filter(id=course_id).first()
        if course:
            return Role.objects.filter(course=course,
                                       user=self.django_user,
                                       role=roles[0]).exists()

    @property
    def is_linked(self):
        return bool(self.django_user)
