from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from ctms.views import (
    MyCoursesView, CreateCourseView, SharedCoursesListView, CourseView, CoursletView, CreateCoursletView,
    CreateUnitView, UnitView,
    UpdateCourseView, DeleteCourseView, EditUnitView, ResponseView, UnitSettingsView, CoursletSettingsView,
    CoursletDeleteView, DeleteUnitView)

urlpatterns = patterns(
    '',
    url(r'^courses/?$', MyCoursesView.as_view(), name='my_courses'),

    url(r'^courses/new/?$', CreateCourseView.as_view(), name='create_course'),
    url(r'^courses/(?P<pk>\d+)/?$', CourseView.as_view(), name='course_view'),
    url(r'^courses/(?P<pk>\d+)/edit/?$', UpdateCourseView.as_view(), name='course_settings'),
    url(r'^courses/(?P<pk>\d+)/delete/?$', DeleteCourseView.as_view(), name='course_delete'),

    # new courslet
    url(r'^courses/(?P<course_pk>\d+)/courslets/new/?$',
        CreateCoursletView.as_view(),
        name='courslet_create'),
    # list courslets
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<pk>\d+)/?$',
        CoursletView.as_view(),
        name='courslet_view'),
    # courslet settings
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<pk>\d+)/settings/?$',
        CoursletSettingsView.as_view(),
        name='courslet_settings'),
    # delete courslet
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<pk>\d+)/delete/?$',
        CoursletDeleteView.as_view(),
        name='courslet_delete'),

    # new unit
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/new/?$',
        CreateUnitView.as_view(),
        name='unit_create'),
    # edit unit
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/edit/?$',
        EditUnitView.as_view(),
        name='unit_edit'),
    # delete unit
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/delete/?$',
        DeleteUnitView.as_view(),
        name='unit_delete'),
    # unit settings
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/settings/?$',
        UnitSettingsView.as_view(),
        name='unit_settings'),

    # responses
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/(?P<pk>\d+)/?$',
        UnitView.as_view(),
        name='unit_view'),
    # response
    url(r'^courses/(?P<course_pk>\d+)/courslets/(?P<courslet_pk>\d+)/unit/(?P<unit_pk>\d+)/response/(?P<pk>\d+)/?$',
        ResponseView.as_view(),
        name='response_view'),



    url(r'^shared_courses/$', SharedCoursesListView.as_view(),
        name='shared_courses'),

)