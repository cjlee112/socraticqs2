from django.conf.urls import url
from django.views.generic import TemplateView
from django.contrib.auth.views import password_reset_confirm, password_reset_complete
from accounts.forms import CustomPasswordResetForm, CustomSetPasswordForm
from accounts.views import custom_password_reset, custom_password_reset_done, resend_email_confirmation_link

from .views import DeleteAccountView, AccountSettingsView, ProfileUpdateView


urlpatterns = [
    url(r'^delete/$', DeleteAccountView.as_view(), name='delete'),
    url(r'^account_deleted/$', TemplateView.as_view(template_name='accounts/account_deleted.html'), name='deleted'),
    url(r'^password_reset/$', custom_password_reset, {
        'template_name': 'accounts/password_reset_form.html',
        'post_reset_redirect': 'accounts:password_reset_done',
        'password_reset_form': CustomPasswordResetForm
    }, name='password_reset'),

    url(r'^resend_email_confirmation_link/$', resend_email_confirmation_link, name='resend_email_confirmation_link'),

    url(r'^password_reset/done/$', custom_password_reset_done,
        {'template_name': 'accounts/password_reset_done.html'},
        name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        {
            'post_reset_redirect': 'accounts:password_reset_complete',
            'template_name': 'accounts/password_reset_confirm.html',
            'set_password_form': CustomSetPasswordForm
        },
        name='password_reset_confirm'),

    url(r'^reset/done/$', password_reset_complete, {
        'template_name': 'accounts/password_reset_complete.html'
    }, name='password_reset_complete'),

    url(r'^profile_update/$', ProfileUpdateView.as_view(), name='profile_update'),

    url(r'^$', AccountSettingsView.as_view(), name='settings'),
]
