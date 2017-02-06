import injections
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from rest_framework.routers import SimpleRouter

from .views import DeleteAccountView, AccountSettingsView

urlpatterns = patterns(
    '',
    url(r'^delete/$', DeleteAccountView.as_view(), name='delete'),
    url(r'^account_deleted/$', TemplateView.as_view(template_name='accounts/account_deleted.html'), name='deleted'),
    url(r'^$', AccountSettingsView.as_view(), name='settings'),
)

