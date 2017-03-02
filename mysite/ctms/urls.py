from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from ctms.views import (
    MyCoursesView, CreateCourseView, SharedCoursesListView, CourseView, CoursletView, CreateCoursletView,
    CreateUnitView, UnitView,
    UpdateCourseView, DeleteCourseView, EditUnitView, ResponseView, UnitSettingsView, CoursletSettingsView,
    CoursletDeleteView, DeleteUnitView, AddUnitEditView, RedirectToCourseletPreview)

urlpatterns = patterns(
    '',
    url(r'^course/?$', MyCoursesView.as_view(), name='my_courses'),

    url(r'^course/new/?$', CreateCourseView.as_view(), name='create_course'),
    url(r'^course/(?P<pk>\d+)/courselet/?$', CourseView.as_view(), name='course_view'),
    url(r'^course/(?P<pk>\d+)/settings/?$', UpdateCourseView.as_view(), name='course_settings'),
    url(r'^course/(?P<pk>\d+)/delete/?$', DeleteCourseView.as_view(), name='course_delete'),

    # go to preview
    url(r'course/(?P<course_pk>\d+)/courslet/(?P<pk>\d+)/preview/?$', RedirectToCourseletPreview.as_view(), name='courselet_preview'),

    # new courslet
    url(r'^course/(?P<course_pk>\d+)/courselet/new/?$',
        CreateCoursletView.as_view(),
        name='courslet_create'),
    # list units
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/units/?$',
        CoursletView.as_view(),
        name='courslet_view'),
    # courslet settings
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/settings/?$',
        CoursletSettingsView.as_view(),
        name='courslet_settings'),
    # delete courslet
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/delete/?$',
        CoursletDeleteView.as_view(),
        name='courslet_delete'),

    # new unit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/new/?$',
        CreateUnitView.as_view(),
        name='unit_create'),
    # edit unit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/edit/?$',
        EditUnitView.as_view(),
        name='unit_edit'),
    # new unit edit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/new_unit_edit/?$',
        AddUnitEditView.as_view(),
        name='add_unit_edit'),
    # delete unit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/delete/?$',
        DeleteUnitView.as_view(),
        name='unit_delete'),
    # unit settings
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/settings/?$',
        UnitSettingsView.as_view(),
        name='unit_settings'),

    # responses
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/response/?$',
        UnitView.as_view(),
        name='unit_view'),
    # response
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courslet_pk>\d+)/unit/(?P<unit_pk>\d+)/response/(?P<pk>\d+)/?$',
        ResponseView.as_view(),
        name='response_view'),

    # shares
    url(r'^shared_course/$', SharedCoursesListView.as_view(),
        name='shared_courses'),
)
