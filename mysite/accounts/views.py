from functools import partial

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import password_reset, password_reset_done
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView
from django.views.generic.base import TemplateView
from django.conf import settings

from accounts.forms import (
    UserForm, InstructorForm, ChangePasswordForm,
    DeleteAccountForm, ChangeEmailForm,
    CreatePasswordForm)
from accounts.models import Instructor
from ctms.views import json_response
from mysite.mixins import NotAnonymousRequiredMixin
from psa.custom_backends import EmailAuth
from psa.custom_django_storage import CustomDjangoStorage, CustomCode
from psa.custom_django_strategy import CustomDjangoStrategy
from .forms import SocialForm


class AccountSettingsView(NotAnonymousRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'

    def get_instructor(self):
        try:
            return self.request.user.instructor
        except Instructor.DoesNotExist:
            return

    def get_password_form_cls(self):
        return ChangePasswordForm if self.request.user.has_usable_password() else CreatePasswordForm

    def get(self, request):
        instructor = self.get_instructor()
        return self.render_to_response(
            dict(
                user_form=UserForm(instance=request.user),
                instructor_form=InstructorForm(instance=instructor),
                password_form=self.get_password_form_cls()(instance=request.user),
                delete_account_form=DeleteAccountForm(instance=request.user),
                email_form=ChangeEmailForm(initial={'email': request.user.email}),
                person=request.user
            )
        )

    def post(self, request):
        instructor = self.get_instructor()
        form_name = {
            'user_form': partial(UserForm, instance=request.user),
            'instructor_form': partial(InstructorForm, instance=instructor),
            'email_form': partial(ChangeEmailForm, initial={'email': request.user.email}),
            'password_form': partial(self.get_password_form_cls(), instance=request.user),
            'delete_account_form': partial(DeleteAccountForm, instance=request.user),
        }

        form_save_part = {
            'user_form': lambda form_obj: partial(form_obj.save),
            'instructor_form': lambda form_obj: partial(form_obj.save),
            'email_form': lambda form_obj: partial(form_obj.save, request, commit=False),
            'password_form': lambda form_obj: partial(form_obj.save),
            'delete_account_form': lambda form_obj: partial(form_obj.save),
        }
        kwargs = {}
        has_errors = False
        non_field_errors_list = []
        do_email_saving = False

        def get_form_changed_data(form):
            data = form.changed_data
            if 'form_id' in form.changed_data:
                data.pop(data.index('form_id'))
            return data

        for form_id, form_cls in form_name.items():
            if form_id in request.POST.getlist('form_id'):
                form = form_cls(data=request.POST)
                changed_data = get_form_changed_data(form)
                if form.is_valid() and changed_data:
                    save = form_save_part[form_id](form)
                    if form_id == 'email_form':
                        do_email_saving = True
                        email_save = save
                    elif form_id == 'password_form':
                        save()
                        update_session_auth_hash(request, request.user)
                    else:
                        save()
                elif changed_data:
                    has_errors = True
                    non_field_errors_list.append(unicode(form.non_field_errors()))
                kwargs[form_id] = form
            else:
                kwargs[form_id] = form_cls()
        if do_email_saving:
            return email_save()
        kwargs['person'] = request.user
        if not has_errors:
            return HttpResponseRedirect(reverse('accounts:settings'))
        else:
            msg = u"Please correct errors below: <br> {}".format(u"<br>".join(non_field_errors_list))
            messages.add_message(request, messages.WARNING, mark_safe(msg))
        return self.render_to_response(
            kwargs
        )


class DeleteAccountView(NotAnonymousRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'

    def post(self, request):
        form = DeleteAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            logout(request)
            return HttpResponseRedirect(reverse('accounts:deleted'))
        return self.render_to_response(
            dict(
                user_form=UserForm(instance=request.user),
                instructor_form=InstructorForm(instance=request.user.instructor),
                password_form=ChangePasswordForm(),
                delete_account_form=form,
                person=request.user
            )
        )


class ProfileUpdateView(NotAnonymousRequiredMixin, CreateView):
    template_name = 'accounts/profile_edit.html'
    model = Instructor
    form_class = SocialForm

    def get_success_url(self):
        return reverse('ctms:my_courses')

    def get_initial(self):
        return {'user': self.request.user}

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'instance': self.get_instance()
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_instance(self):
        try:
            instructor = self.request.user.instructor
        except self.request.user._meta.model.instructor.RelatedObjectDoesNotExist:
            instructor = None
        return instructor

    def get(self, request):
        instructor = self.get_instance()
        if instructor is not None and instructor.institution:
            return redirect(self.get_success_url())
        else:
            form = self.get_form()
            return self.render_to_response({'form': form})


@csrf_protect
def custom_password_reset(request,
                          template_name='registration/password_reset_form.html',
                          email_template_name='registration/password_reset_email.html',
                          subject_template_name='registration/password_reset_subject.txt',
                          password_reset_form=PasswordResetForm,
                          token_generator=default_token_generator,
                          post_reset_redirect=None,
                          from_email=settings.EMAIL_FROM,
                          current_app=None,
                          extra_context=None,
                          html_email_template_name=None):
    response = password_reset(request,
                              template_name=template_name,
                              email_template_name=email_template_name,
                              subject_template_name=subject_template_name,
                              password_reset_form=password_reset_form,
                              token_generator=token_generator,
                              post_reset_redirect=post_reset_redirect,
                              from_email=from_email,
                              current_app=current_app,
                              extra_context=extra_context,
                              html_email_template_name=html_email_template_name)
    if request.method == 'POST' and isinstance(response, HttpResponseRedirect):
        request.session['anonym_user_email'] = request.POST.get('email')
    return response


def custom_password_reset_done(request,
                               template_name='registration/password_reset_done.html',
                               current_app=None, extra_context=None):
    if extra_context:
        extra_context.update({'anonym_user_email': request.session.get('anonym_user_email')})
    else:
        extra_context = {'anonym_user_email': request.session.get('anonym_user_email')}
    return password_reset_done(request,
                               template_name=template_name,
                               current_app=current_app, extra_context=extra_context)


def resend_email_confirmation_link(request):
    email = request.POST.get('email')
    session_email = request.session.get('resend_user_email')
    cc_id = request.session.get('cc_id')

    if session_email != email:
        raise Http404()

    if request.user.is_authenticated():
        logout(request)
        request.session['resend_user_email'] = session_email
        request.session['cc_id'] = cc_id

    def resend(request):
        if CustomCode.objects.filter(email=email, verified=True).count():
            return {'ok': 0, 'error': 'Email {} already verified!'.format(email)}
        try:
            post = request.POST.dict()
            cc = CustomCode.objects.filter(pk=request.session.get('cc_id')).first()
            fields = ['first_name', 'last_name', 'institution']
            if cc:
                for field in fields:
                    post[field] = getattr(cc, field, '')
            request.POST = post

            strategy = CustomDjangoStrategy(CustomDjangoStorage, request=request)
            strategy.send_email_validation(EmailAuth, email)
            return {'ok': 1}
        except Exception as e:
            return {'ok': 0, 'error': e.message}

    return json_response(resend(request))