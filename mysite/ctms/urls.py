from django.conf.urls import url
from django.urls import include, path
from ctms.views import (
    MyCoursesView, CreateCourseView, SharedCoursesListView, CourseView,
    CoursletView, CreateCoursletView, CreateCoursletWithPBView,
    CreateUnitView, UnitView,
    UpdateCourseView, DeleteCourseView, ResponseView, UnitSettingsView, CoursletSettingsView,
    CoursletDeleteView, DeleteUnitView, CreateEditUnitView, RedirectToCourseletPreviewView, RedirectToAddUnitsView,
    InvitesListView, JoinCourseView, ResendInviteView, DeleteInviteView, EmailSentView,
    ReorderUnits, Onboarding, OnboardingBP1, OnboardingBP2, BestPracticesCourseView, BestPracticesCourseletView,
    BestPracticeCalculation, BestPracticeActivation, BestPracticePreCalculation)

app_name = 'ctms'

urlpatterns = [
    url(r'^$', MyCoursesView.as_view(), name='my_courses'),

    url(r'^course/new/?$', CreateCourseView.as_view(), name='create_course'),
    url(r'^course/(?P<pk>\d+)/courselet/?$', CourseView.as_view(), name='course_view'),
    url(r'^course/(?P<pk>\d+)/settings/?$', UpdateCourseView.as_view(), name='course_settings'),
    url(r'^course/(?P<pk>\d+)/best-practices/?$', BestPracticesCourseView.as_view(), name='course_best_practice'),
    url(r'^course/(?P<pk>\d+)/delete/?$', DeleteCourseView.as_view(), name='course_delete'),
    url(r'^onboarding/$', Onboarding.as_view(), name='onboarding'),
    url(r'^onboarding/bp1$', OnboardingBP1.as_view(), name='onboarding_bp1'),
    url(r'^onboarding/bp2$', OnboardingBP2.as_view(), name='onboarding_bp2'),
    path('bp/<int:pk>/calculation/', BestPracticePreCalculation.as_view(), name='template-calculation'),
    path('course/<int:course_pk>/bp/<int:pk>/calculation/', BestPracticeCalculation.as_view(), name='calculation'),
    path('course/<int:course_pk>/bp/<int:pk>/activation/', BestPracticeActivation.as_view(), name='activation'),


    # go to preview
    url(
        r'course/(?P<course_pk>\d+)/courslet/(?P<pk>\d+)/preview/?$',
        RedirectToCourseletPreviewView.as_view(),
        name='courselet_preview'
    ),

    # new courslet
    url(r'^course/(?P<course_pk>\d+)/courselet/new/?$',
        CreateCoursletView.as_view(),
        name='courslet_create'),
    # new courslet with BP
    url(r'^course/(?P<course_pk>\d+)/bestpractise/(?P<best_practise_pk>\d+)/courselet/new/?$',
        CreateCoursletWithPBView.as_view(),
        name='courslet_create_with_bp'),
    # list units
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/units/?$',
        CoursletView.as_view(),
        name='courslet_view'),
    # courslet settings
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/settings/?$',
        CoursletSettingsView.as_view(),
        name='courslet_settings'),
    # courslet best practices
    path('course/<int:course_pk>/courselet/<int:courselet_pk>/best-practices/',
        BestPracticesCourseletView.as_view(),
        name='courselet_best_practice'),
    path('course/<int:course_pk>/courselet/<int:courselet_pk>/bp/<int:pk>/calculation/', BestPracticeCalculation.as_view(), name='courselet_bp_calculation'),
    path('course/<int:course_pk>/courselet/<int:courselet_pk>/bp/<int:pk>/activation/', BestPracticeActivation.as_view(), name='courselet_bp_activation'),
    # delete courslet
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/delete/?$',
        CoursletDeleteView.as_view(),
        name='courslet_delete'),
    # reorder units
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/reorder/?$',
        (ReorderUnits.as_view()),
        name='courslet_reorder'),

    # new unit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/new/?$',
        CreateUnitView.as_view(),
        name='unit_create'),
    # unit edit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/(?P<pk>\d+)/edit/?$',
        CreateEditUnitView.as_view(),
        name='unit_edit'),
    # delete unit
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/(?P<pk>\d+)/delete/?$',
        DeleteUnitView.as_view(),
        name='unit_delete'),
    # unit settings
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/(?P<pk>\d+)/settings/?$',
        UnitSettingsView.as_view(),
        name='unit_settings'),

    # responses
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/(?P<pk>\d+)/response/?$',
        UnitView.as_view(),
        name='unit_view'),
    # response
    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<courselet_pk>\d+)/unit/(?P<unit_pk>\d+)/response/(?P<pk>\d+)/?$',
        ResponseView.as_view(),
        name='response_view'),

    # shares
    url(r'^shared_courses/$', SharedCoursesListView.as_view(),
        name='shared_courses'),
    # url(r'^share_course/$', CreateSharedCourseView.as_view(),
    #     name='cr_share_course'),

    # url(r'^course/(?P<pk>\d+)/share_course/$', InvitesListView.as_view(),
    #     name='share_course'),
    url(r'^course/(?P<pk>\d+)/share_courselet/tester/(?P<courselet_pk>\d+)?/$',
        InvitesListView.as_view(template_name='ctms/invite_tester_list.html'), name='courselet_invite'),

    url(r'^course/(?P<pk>\d+)/share_courselet/student/(?P<courselet_pk>\d+)?/$',
        InvitesListView.as_view(template_name='ctms/invite_student_list.html'), name='courselet_invite_student'),

    # url(r'^course/(?P<pk>\d+)/invite/?$', InvitesListView.as_view(), name='course_invite'),
    url(r'^invites/(?P<code>\w+)/join/$', JoinCourseView.as_view(), name='tester_join_course'),
    url(r'^invites/(?P<code>\w+)/resend/$', ResendInviteView.as_view(), name='resend_invite'),
    url(r'^invites/(?P<code>\w+)/delete/$', DeleteInviteView.as_view(), name='delete_invite'),

    url(r'^email_sent/(?P<backend>\w+)?', EmailSentView.as_view(), name='email_sent'),

    url(r'^course/(?P<course_pk>\d+)/courselet/(?P<pk>\d+)/add_units_chat/?$',
        RedirectToAddUnitsView.as_view(),
        name='add_units_chat'),
]
