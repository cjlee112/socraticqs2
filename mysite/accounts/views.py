from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View
from django.core.urlresolvers import reverse
from functools import partial
from accounts.forms import UserForm, InstructorForm, ChangePasswordForm, DeleteAccountForm, ChangeEmailForm
from mysite.mixins import LoginRequiredMixin


class AccountSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            'accounts/settings.html',
            dict(
                user_form=UserForm(instance=request.user),
                instructor_form=InstructorForm(instance=request.user.instructor),
                password_form=ChangePasswordForm(),
                delete_account_form=DeleteAccountForm(instance=request.user),
                email_form=ChangeEmailForm(initial={'email': request.user.email}),
                person=request.user
            )
        )

    def post(self, request):
        form_name = {
            'user_form': partial(UserForm, instance=request.user),
            'instructor_form': partial(InstructorForm, instance=request.user.instructor),
            'email_form': partial(ChangeEmailForm, initial={'email': request.user.email}),
            'password_form': partial(ChangePasswordForm, instance=request.user),
            'delete_account_form': partial(DeleteAccountForm, instance=request.user),
        }
        kwargs = {}
        has_errors = False

        for form_id, form_cls in form_name.items():
            if form_id in request.POST.getlist('form_id'):
                form = form_cls(data=request.POST)
                if form.is_valid():
                    if form_id == 'email_form':
                        resp = form.save(request, commit=False)
                        # print user.email
                    else:
                        form.save()
                else:
                    has_errors = True
                kwargs[form_id] = form
            else:
                kwargs[form_id] = form_cls()

        kwargs['person'] = request.user
        if not has_errors:
            return HttpResponseRedirect(reverse('accounts:settings'))
        return render(
            request,
            'accounts/settings.html',
            kwargs
        )

class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request):
        form = DeleteAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            new_user = form.save()
            logout(request)
            return HttpResponseRedirect(reverse('accounts:deleted'))
        return render(
            request,
            'accounts/settings.html',
            dict(
                user_form=UserForm(instance=request.user),
                instructor_form=InstructorForm(instance=request.user.instructor),
                password_form=ChangePasswordForm(),
                delete_account_form=form,
                person=request.user
            )
        )


