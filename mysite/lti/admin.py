from django.contrib import admin
from django.forms.models import ModelForm

from lti.models import LTIUser, CourseRef, LtiConsumer, OutcomeService, GradedLaunch


class LtiConsumerForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(LtiConsumerForm, self).__init__(*args, **kwargs)

        class Meta:
            model = LtiConsumer

    def clean(self):
        cleaned_data = self.cleaned_data
        instance_guid = cleaned_data.get('instance_guid')

        if not instance_guid:
            cleaned_data['instance_guid'] = None

        return cleaned_data


class LTIUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'lti_consumer', 'django_user')


class CourseRefAdmin(admin.ModelAdmin):
    list_display = ('context_id', 'course', 'date')
    filter_horizontal = ('instructors',)


class LtiConsumerAdmin(admin.ModelAdmin):
    """Admin for LTI Consumer"""
    form = LtiConsumerForm

    search_fields = ('consumer_name', 'consumer_key', 'instance_guid', 'expiration_date')
    list_display = ('consumer_name', 'consumer_key', 'instance_guid', 'expiration_date')


class OutcomeServiceAdmin(admin.ModelAdmin):
    list_display = ('lis_outcome_service_url',)


class GradedLaunchAdmin(admin.ModelAdmin):
    list_display = ('user', 'course_id', 'outcome_service', 'lis_result_sourcedid',)


admin.site.register(LTIUser, LTIUserAdmin)
admin.site.register(CourseRef, CourseRefAdmin)
admin.site.register(OutcomeService, OutcomeServiceAdmin)
admin.site.register(GradedLaunch, GradedLaunchAdmin)
