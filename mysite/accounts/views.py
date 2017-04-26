from functools import partial
from django.contrib import messages

from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import View, CreateView
from django.core.urlresolvers import reverse
from django.views.generic.base import TemplateView

from accounts.forms import (
    UserForm, InstructorForm, ChangePasswordForm,
    DeleteAccountForm, ChangeEmailForm,
    CreatePasswordForm)
from accounts.models import Instructor
from mysite.mixins import LoginRequiredMixin, NotAnonymousRequiredMixin
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

        for form_id, form_cls in form_name.items():
            if form_id in request.POST.getlist('form_id'):
                form = form_cls(data=request.POST)
                if form.is_valid():
                    save = form_save_part[form_id](form)
                    rsp = save()
                    if form_id == 'email_form':
                        return rsp
                else:
                    has_errors = True
                kwargs[form_id] = form
            else:
                kwargs[form_id] = form_cls()

        kwargs['person'] = request.user
        if not has_errors:
            return HttpResponseRedirect(reverse('accounts:settings'))
        else:
            messages.add_message(request, messages.WARNING, "Please correct errors below")
        return self.render_to_response(
            kwargs
        )

class DeleteAccountView(NotAnonymousRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'
    def post(self, request):
        form = DeleteAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            new_user = form.save()
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
        return {
           'user': self.request.user,
        }

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
        except self.request.user._meta.model.instructor.RelatedObjectDoesNotExist as e:
            instructor = None
        return instructor


    def get(self, request):
        instructor = self.get_instance()
        if instructor is not None and instructor.institution:
            return redirect(self.get_success_url())
        else:
            form = self.get_form()
            return self.render_to_response({'form': form})
