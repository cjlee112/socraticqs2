import json
from django.db import models
from django.contrib.auth import login
from django.contrib.auth.models import User

from social.apps.django_app.default.models import UserSocialAuth

from ct.models import Role, Course


class LTIUser(models.Model):
    """Model for LTI user

    Created for Moodle LMS.
    Intended to link to Django user in socraticqs2.
    """
    user_id = models.CharField(max_length=255, blank=False)
    consumer = models.CharField(max_length=64, blank=True)
    extra_data = models.TextField(max_length=1024, blank=False)
    django_user = models.ForeignKey(User, null=True, related_name='lti_auth')
    course_id = models.IntegerField()

    class Meta:
        unique_together = ('user_id', 'consumer', 'course_id')

    def create_links(self):
        extra_data = json.loads(self.extra_data)
        username = extra_data.get('lis_person_name_full', self.user_id)
        first_name = extra_data.get('lis_person_name_given', '')
        last_name = extra_data.get('lis_person_name_family', '')
        email = extra_data.get('lis_person_contact_email_primary', '').lower()

        if email:
            social = UserSocialAuth.objects.filter(provider='email',
                                                   uid=email)
            if social:
                django_user = social[0].user
            else:
                django_user = User.objects.filter(email=email)
                if django_user:
                    django_user = django_user[0]
                else:
                    django_user = User.objects.get_or_create(username=username,
                                                             defaults={
                                                                 'first_name': first_name,
                                                                 'last_name': last_name,
                                                                 'email': email
                                                             })[0]
                social = UserSocialAuth(user=django_user,
                                        provider='email',
                                        uid=email,
                                        extra_data=extra_data)
                social.save()
        else:
            django_user = User.objects.get_or_create(username=username,
                                                     defaults={
                                                         'first_name': first_name,
                                                         'last_name': last_name,
                                                     })[0]
        self.django_user = django_user
        self.save()

    def login(self, request):
        if self.django_user:
            self.django_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, self.django_user)

    def enroll(self, roles, course_id):
        if not isinstance(roles, list):
            roles = roles.split(',')
        course = Course.objects.filter(id=course_id)
        if course:
            course = course[0]
            for role in roles:
                Role.objects.get_or_create(course=course,
                                           user=self.django_user,
                                           role=role)

    def is_enrolled(self, roles, course_id):
        if not isinstance(roles, list):
            roles = roles.split(',')
        course = Course.objects.filter(id=course_id)
        if course:
            course = course[0]
        return Role.objects.filter(course=course,
                                   user=self.django_user,
                                   role=roles[0]).exists()

    @property
    def is_linked(self):
        return bool(self.django_user)
