from django.conf.urls import url, include

from pages.views import interested_form, BecomeInstructor

urlpatterns = (
    url(r'^become_instructor_form/?$', BecomeInstructor.as_view(), name='become_instructor_form'),
    url(r'^interested-form/?$', interested_form, name='interested-form'),
)
