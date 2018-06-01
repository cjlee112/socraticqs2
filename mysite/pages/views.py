from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView
from django.conf import settings

from accounts.models import Instructor
from mysite.mixins import NewLoginRequiredMixin
from pages.forms import InterestedModelForm, BecomeInstructorForm
from pages.tasks import form_send


def interested_form(request):
    obj = InterestedModelForm(request.POST)
    if obj.is_valid():
        obj.save()
        form_send(obj.clean())
        return JsonResponse({'success': 'Thanks for contacting us! We will get in touch with you shortly.'})
    else:
        return JsonResponse({'error': 'Something went wrong. Please try again later.'})


class BecomeInstructor(NewLoginRequiredMixin, CreateView): # CourseCoursletUnitMixin
    template_name = 'pages/become_instructor.html'
    model = Instructor
    NEED_INSTRUCTOR = False
    form_class = BecomeInstructorForm
    success_url = 'ctms:my_courses'

    def get_next_page(self):
        return self.request.POST.get('next') or self.request.GET.get('next')

    def am_i_instructor(self):
        try:
            self.request.user.instructor
            return True
        except Instructor.DoesNotExist:
            return False

    def get(self, request):
        return redirect(self.success_url if self.am_i_instructor() else settings.BECOME_INSTRUCTOR_URL)

    def post(self, request):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if not self.am_i_instructor() and form.is_valid():
            if form.cleaned_data['agree']:
                instructor = form.save(commit=False)
                instructor.user = self.request.user
                instructor.save()
        return redirect(self.get_next_page() or self.success_url)
