from django.contrib import admin
from django.forms.models import ModelForm

from lti.models import LTIUser, CourseRef, LtiConsumer


class LtiConsumerForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(LtiConsumerForm, self).__init__(*args, **kwargs)

        class Meta:
            model = LtiConsumerAdmin

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

    search_fields = ('consumer_name', 'consumer_key', 'instance_guid')
    list_display = ('consumer_name', 'consumer_key', 'instance_guid')


admin.site.register(LTIUser, LTIUserAdmin)
admin.site.register(CourseRef, CourseRefAdmin)
admin.site.register(LtiConsumer, LtiConsumerAdmin)
