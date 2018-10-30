import waffle
import json
from uuid import uuid4

from django.contrib.sites.models import Site
from django.http import JsonResponse
from django.http.response import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.db import models
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from social_core.backends.utils import load_backends

from accounts.models import Instructor

from core.common import onboarding
from core.common.mongo import c_onboarding_status
from core.common.utils import get_onboarding_steps, get_onboarding_percentage, \
    get_onboarding_setting, update_onboarding_step

from chat.models import EnrollUnitCode
from ct.forms import LessonRoleForm

from ctms.forms import (
    CreateEditUnitForm,
    ErrorModelFormSet,
    CreateEditUnitAnswerForm,
    CreateUnitForm)
from ct.models import Course, CourseUnit, Unit, UnitLesson, Lesson, Response, Role, Concept
from ctms.forms import CourseForm, CreateCourseletForm, EditUnitForm, InviteForm
from ctms.models import Invite
from mysite.mixins import NewLoginRequiredMixin
from psa.forms import SignUpForm, EmailLoginForm
from .utils import Memoize


memoize = Memoize()


def json_response(x):
    return HttpResponse(json.dumps(x, sort_keys=True, indent=2),
                        content_type='application/json; charset=UTF-8')


class CourseCoursletUnitMixin(View):
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'
    NEED_INSTRUCTOR = True
    response_class = TemplateResponse

    def render(self, template_name, context):
        return self.response_class(
            request=self.request,
            template=template_name,
            context=context,
        )

    def dispatch(self, request, *args, **kwargs):
        if self.NEED_INSTRUCTOR and not self.am_i_instructor():
            return redirect(settings.BECOME_INSTRUCTOR_URL)
        return super(CourseCoursletUnitMixin, self).dispatch(request, *args, **kwargs)

    def am_i_course_owner(self):
        course = self.get_course()
        return course and course.addedBy != self.request.user or False

    def am_i_instructor(self):
        try:
            instructor = self.request.user.instructor
            return True
        except Instructor.DoesNotExist:
            return False

    def get_courses_where_im_instructor(self):
        return Course.objects.filter(role__role=Role.INSTRUCTOR, role__user=self.request.user)

    def get_course(self):
        return Course.objects.filter(id=self.kwargs.get(self.course_pk_name)).first()

    def get_courslet(self):
        return CourseUnit.objects.filter(id=self.kwargs.get(self.courslet_pk_name)).first()

    def get_unit_lesson(self):
        return UnitLesson.objects.filter(id=self.kwargs.get(self.unit_pk_name)).first()

    def get_context_data(self, **kwargs):
        try:
            context = super(CourseCoursletUnitMixin, self).get_context_data(**kwargs)
        except AttributeError:
            context = kwargs
        context.update(self.kwargs)
        return context

    def get_my_courses(self):
        return Course.objects.filter(
            models.Q(addedBy=self.request.user)
        )

    def get_my_or_shared_with_me_courses(self):
        return Course.objects.filter(
            models.Q(addedBy=self.request.user) |
            models.Q(role__role=Role.INSTRUCTOR, role__user=self.request.user)
        ).distinct()

    def get_my_or_shared_with_me_course_units(self):
        return CourseUnit.objects.filter(
            models.Q(addedBy=self.request.user) |
            models.Q(course__role__role=Role.INSTRUCTOR, course__role__user=self.request.user) |
            models.Q(course__addedBy=self.request.user)
        ).distinct()

    def get_courselets_by_course(self, course):
        return course.courseunit_set.filter(order__isnull=False)

    def get_units_by_courselet(self, courselet):
        cache_key = memoize.cache_key('get_units_by_courselet', courselet)
        cached = cache.get(cache_key)
        if cached:
            return cached
        # UnitLesson
        courslet_units = courselet.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by(
            'order'
        ).annotate(
            responses_count=models.Sum(
                models.Case(
                    models.When(models.Q(response__is_test=False, response__is_preview=False), then=1),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        )
        for unit in courslet_units:
            unit.url = reverse(
                'ctms:unit_view' if unit.lesson.kind == Lesson.ORCT_QUESTION and unit.response_set.exists() else 'ctms:unit_edit',
                kwargs={
                    'course_pk': courselet.course.id,
                    'courslet_pk': courselet.id,
                    'pk': unit.id
                }
            )
        cache.set(cache_key, courslet_units, 60)
        return courslet_units

    def get_invite_by_code_request_or_404(self, code):
        return Invite.get_by_user_or_404(self.request.user, code=code)


class FormSetBaseView(object):
    formset_prefix = None

    def get_formset_class(self):
        return self.formset_class

    def get_formset(self, formset_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        if formset_class is None:
            formset_class = self.get_formset_class()
        return formset_class(**self.get_formset_kwargs())

    def formset_valid(self, formset):
        pass

    def formset_invalid(self, formset, *args, **kwargs):
        pass

    def get_formset_prefix(self):
        """
        Returns the prefix to use for forms on this view
        """
        return self.formset_prefix

    def get_formset_queryset(self):
        pass

    def get_formset_kwargs(self):
        kwargs = {
            'initial': self.get_formset_initial(),
            'prefix': self.get_formset_prefix(),
            'queryset': self.get_formset_queryset(),
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_formset_initial(self):
        return [{}]


class MyCoursesView(NewLoginRequiredMixin, CourseCoursletUnitMixin, ListView):
    template_name = 'ctms/my_courses.html'
    model = Course

    def get_context_data(self, **kwargs):
        my_courses = self.get_my_courses()
        courses_shared_by_role = self.get_courses_where_im_instructor()

        return {
            'my_courses': my_courses,
            'instructor_role_courses': courses_shared_by_role

        }

    def get(self, request, *args, **kwargs):
        my_courses = self.get_my_courses()
        if waffle.switch_is_active('ctms_onboarding_enabled') and get_onboarding_percentage(request.user.id) != 100:
            return redirect('ctms:onboarding')
        if not my_courses and not self.request.user.invite_set.all():
            # no my_courses and no shared courses
            return redirect('ctms:create_course')
        if not my_courses and self.request.user.invite_set.all():
            # no my_courses and present more that zero shared course
            return redirect('ctms:shared_courses')
        return super(MyCoursesView, self).get(request, *args, **kwargs)

    def post(self, request):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.addedBy = request.user
            course.save()
            return redirect(reverse('ctms:course_view', kwargs={'course_id': course.id}))
        return self.render(
            'ctms/my_courses.html',
            {'course_form': form}
        )


class CreateCourseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    template_name = 'ctms/my_courses.html'
    model = Course
    fields = ['title']
    # form_class = CourseForm

    def get(self, request, *args, **kwargs):
        if not self.am_i_instructor():
            raise Http404()
        return super(CreateCourseView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.am_i_instructor():
            raise Http404()
        return super(CreateCourseView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.addedBy = self.request.user
        self.object = form.save()
        Role.objects.create(course=self.object, role=Role.INSTRUCTOR, user=self.request.user)
        return redirect(reverse('ctms:course_view', kwargs={'pk': self.object.id}))


class UpdateCourseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    template_name = 'ctms/course_form.html'
    model = Course
    fields = ['title', 'trial']

    def get(self, request, *args, **kwargs):
        if not self.am_i_instructor():
            raise Http404()
        return super(UpdateCourseView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.am_i_instructor():
            raise Http404()
        return super(UpdateCourseView, self).post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if 'pk' in self.kwargs:
            course = Course.objects.filter(
                models.Q(id=self.kwargs.get('pk')) &
                (
                    models.Q(addedBy=self.request.user) |
                    models.Q(role__role=Role.INSTRUCTOR, role__user=self.request.user)
                )
            ).distinct().first()
            if not course:
                raise Http404()
            return course

    def form_valid(self, form):
        form.instance.addedBy = self.request.user
        messages.add_message(self.request, messages.SUCCESS, "Course successfully updated")
        return super(UpdateCourseView, self).form_valid(form)

    def get_success_url(self):
        return reverse('ctms:course_view', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        kwargs = super(UpdateCourseView, self).get_context_data(**kwargs)
        kwargs.update(self.kwargs)
        kwargs['domain'] = 'https://{0}'.format(Site.objects.get_current().domain)
        kwargs['object'] = self.object
        return kwargs


class DeleteCourseView(NewLoginRequiredMixin, DeleteView):
    """
    Delete course view
    Delete course can only owner.
    """
    model = Course

    def get_queryset(self):
        return Course.objects.filter(addedBy=self.request.user)

    def get_success_url(self):
        return reverse('ctms:my_courses')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteCourseView, self).delete(request, *args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, "Course successfully deleted")
        return response


class SharedCoursesListView(NewLoginRequiredMixin, ListView):
    context_object_name = 'shared_courses'
    template_name = 'ctms/sharedcourse_list.html'
    model = Invite
    queryset = Invite.objects.all()

    def get_queryset(self):
        qs = super(SharedCoursesListView, self).get_queryset()
        q = qs.shared_for_me(self.request)
        return q

    def get_context_data(self, **kwargs):
        kwargs = super(SharedCoursesListView, self).get_context_data(**kwargs)
        kwargs['instructor_role_courses'] = Course.objects.filter(
            role__role=Role.INSTRUCTOR, role__user=self.request.user
        )
        return kwargs


class CourseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = Course
    template_name = 'ctms/course_detail.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        # return self.object.courslet_view(published_only=False)
        return self.get_my_or_shared_with_me_courses()

    def get_context_data(self, **kwargs):
        kwargs.update({
            'courslets': self.object.get_course_units(publishedOnly=False)
        })
        return kwargs


class CoursletView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = CourseUnit
    template_name = 'ctms/courselet_detail.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'pk'
    unit_pk_name = None

    def get_queryset(self):
        # UnitLesson
        return self.get_my_or_shared_with_me_course_units().filter(
            course=self.get_course()
        )

    def get_context_data(self, **kwargs):
        kwargs.update({
            'u_lessons': self.get_units_by_courselet(self.object)
        })
        kwargs.update(self.kwargs)
        return kwargs


class CreateCoursletView(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Unit
    template_name = 'ctms/courselet_form.html'
    fields = ('title',)
    form = CreateCourseletForm

    def get_success_url(self):
        return reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.get_course().pk,
                'pk': self.object.course_unit.id
            }
        )

    def get_queryset(self):
        return Unit.objects.filter(
            courseunit__course=self.kwargs.get('course_pk'),
            courseunit__course__addedBy=self.request.user
        )

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.addedBy = self.request.user
        self.object.save()
        self.object.course_unit = CourseUnit.objects.create(
            unit=self.object,
            course=self.get_course(),
            addedBy=self.request.user,
            order=0,
        )
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(CreateCoursletView, self).get_context_data(**kwargs)
        context.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return context


class UnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    template_name = 'ctms/unit_detail.html'
    model = UnitLesson

    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'

    def get_queryset(self):
        return self.model.objects.filter(addedBy=self.request.user)

    def get_context_data(self, **kwargs):
        super(UnitView, self).get_context_data(**kwargs)
        course = self.get_course()
        courslet = self.get_courslet()
        is_trial = self.request.GET.get('is_trial') in ['true', 'True', '1']
        responses = self.object.response_set.filter(is_trial=is_trial).order_by('-atime')
        # Onboarding step 7, haven't resolved yet, need to decide.
        # if responses and course.id == get_onboarding_setting(onboarding.INTRODUCTION_COURSE_ID):
        #     update_onboarding_step(onboarding.STEP_7, self.request.user.id)
        kwargs.update({
            'course': course,
            'courslet': courslet,
            'responses': responses,
            'unit': self.get_object(),
            'is_trial': is_trial
        })
        kwargs.update(self.kwargs)
        self.request.session['unitID'] = kwargs['unit'].id
        return kwargs


class CreateUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Lesson
    form_class = CreateUnitForm
    template_name = 'ctms/create_unit_form.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'

    def post(self, request, *args, **kwargs):
        """
        Post handler for creating Unit
        Unit can create only course owner (Course.addedBy field)
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        course = self.get_course()
        if course.addedBy != self.request.user:
            raise Http404()
        return super(CreateUnitView, self).post(request, *args, **kwargs)


    def get_success_url(self):
        return reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_course().id,
                'courslet_pk': self.get_courslet().id,
                'pk': self.object.unit_lesson.id
            }
        )

    def form_valid(self, form):
        courslet = self.get_courslet()
        unit = courslet.unit
        self.object = Lesson(title=form.cleaned_data['title'], text='',
                             kind=Lesson.ORCT_QUESTION, addedBy=self.request.user)
        self.object.save()
        self.object.treeID = self.object.pk
        self.object.save()
        # create UnitLesson with blank answer for this unit
        unit_lesson = UnitLesson.create_from_lesson(self.object, unit, order='APPEND', addAnswer=False)

        self.object.unit_lesson = unit_lesson
        cache.delete(memoize.cache_key('get_units_by_courselet', courslet))
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(CreateUnitView, self).get_context_data(**kwargs)
        context.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return context


class EditUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    model = UnitLesson
    template_name = 'ctms/unit_form.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'
    form_class = EditUnitForm

    def get_object(self, queryset=None):
        """
        Only course owner can edit Units in this course.
        :param queryset:
        :return:
        """
        course, ul = self.get_course(), self.get_unit_lesson()
        if not course.addedBy == self.request.user:
            raise Http404()
        self.object = self.get_unit_lesson().lesson
        return self.object

    def get_success_url(self):
        return reverse('ctms:unit_view', kwargs=self.kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=True)
        # self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "Unit successfully updated")
        cache.delete(memoize.cache_key('get_units_by_courselet', self.get_courslet()))
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return kwargs


class ResponseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = Response
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'
    template_name = 'ctms/response_detail.html'

    def get_queryset(self):
        course = self.get_course()
        if not course.addedBy == self.request.user:
            raise Http404()
        return super(ResponseView, self).get_queryset()

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        return kwargs


class CoursletSettingsView(NewLoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    model = Unit
    fields = ('title', 'is_show_will_learn')
    course_pk_name = 'course_pk'
    courslet_pk_name = 'pk'
    template_name = 'ctms/courslet_settings.html'

    def get_object(self, queryset=None):
        if queryset:
            return queryset.get(pk=self.kwargs.get('pk')).unit
        else:
            course_unit = self.get_my_or_shared_with_me_course_units().filter(pk=self.kwargs.get('pk')).first()
            if not course_unit:
                raise Http404()
            return course_unit.unit

    def get_success_url(self):
        return reverse('ctms:courslet_view', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super(CoursletSettingsView, self).get_context_data(**kwargs)
        context.update(self.kwargs)
        courslet = self.get_courslet()
        context.update({
            'course': self.get_course(),
            'courslet': courslet,
            'domain': 'https://{0}'.format(Site.objects.get_current().domain),
            'enroll_code': EnrollUnitCode.get_code(courslet)
        })
        return context

    def form_valid(self, form):
        response = super(CoursletSettingsView, self).form_valid(form)
        messages.add_message(self.request, messages.SUCCESS, "Courselet successfully updated")
        return response

    def post(self, request, *args, **kwargs):
        task = request.POST.get('task')
        if task:
            cu = self.get_courslet()
            if task == 'release':
                cu.releaseTime = timezone.now()
            if task == 'unrelease':
                cu.releaseTime = None
            cu.save()
            return redirect(self.get_success_url())
        else:
            return super(CoursletSettingsView, self).post(request, *args, **kwargs)




class CoursletDeleteView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    model = CourseUnit
    template_name = 'ctms/courselet_confirm_delete.html'
    courslet_pk_name = 'pk'

    def get_object(self, queryset=None):
        if queryset:
            return super(CoursletDeleteView, self).get_object(
                queryset=queryset.filter(addedBy=self.request.user)
            )
        courselet = self.get_courslet()
        if courselet and courselet.addedBy == self.request.user:
            return courselet
        raise Http404()

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'course': self.get_course(),
            'courslet': self.get_courslet(),
        })
        return kwargs

    def get_success_url(self):
        course = self.get_course()
        if course:
            return reverse('ctms:course_view', kwargs={'pk': course.id})
        return reverse('ctms:my_courses')

    def delete(self, request, *args, **kwargs):
        response = super(CoursletDeleteView, self).delete(request, *args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, "Courselet successfully deleted")
        return response


class DeleteUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    model = UnitLesson
    unit_pk_name = 'pk'

    def get_object(self, queryset=None):
        if queryset:
            return super(DeleteUnitView, self).get_queryset(
                queryset=queryset.filter(addedBy=self.request.user)
            )
        ul = self.get_unit_lesson()
        if ul and ul.addedBy == self.request.user:
            return ul
        raise Http404()

    def get_success_url(self):
        course = self.get_course()
        courslet = self.get_courslet()
        if course and courslet:
            return reverse('ctms:courslet_view', kwargs={
                'course_pk': course.id,
                'pk': courslet.id
            })
        return reverse('ctms:my_courses')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteUnitView, self).delete(request, *args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, "Unit successfully deleted")
        cache.delete(memoize.cache_key('get_units_by_courselet', self.get_courslet()))
        return response


class UnitSettingsView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = UnitLesson
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'
    template_name = 'ctms/unit_settings.html'

    def post(self, request, *args, **kwargs):
        ul = self.get_unit_lesson()
        roleForm = LessonRoleForm('', self.request.POST)
        if roleForm.is_valid():
            if roleForm.cleaned_data['role'] == UnitLesson.RESOURCE_ROLE:
                ul.order = None
                ul.save()
                ul.unit.reorder_exercise()
            elif ul.order is None:
                ul.unit.append(ul, self.request.user)
            cache.delete(memoize.cache_key('get_units_by_courselet', self.get_courslet()))
        return redirect(reverse(
            "ctms:unit_settings",
            kwargs=self.kwargs)
        )

    def get_object(self, queryset=None):
        ul = self.get_unit_lesson()
        if ul and ul.addedBy == self.request.user:
            return ul.lesson
        raise Http404()

    def get_context_data(self, **kwargs):
        kw = super(UnitSettingsView, self).get_context_data(**kwargs)
        kw.update(self.kwargs)
        ul = self.get_unit_lesson()
        if ul.order is not None:
            initial = UnitLesson.LESSON_ROLE
        else:
            initial = UnitLesson.RESOURCE_ROLE
        roleForm = LessonRoleForm(initial)
        kw.update({
            'unit_lesson': ul,
            'course': self.get_course(),
            'courslet': self.get_courslet(),
            'unit': self.get_object(),
            'role_form': roleForm
        })
        return kw




class CreateEditUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, FormSetBaseView, UpdateView):
    model = Lesson
    form_class = CreateEditUnitForm
    formset_class = ErrorModelFormSet
    unit_pk_name = 'pk'
    template_name = 'ctms/unit_edit.html'
    HANDLE_FORMSET = True

    def get_success_url(self):
        return reverse('ctms:unit_edit', kwargs={
            'course_pk': self.kwargs['course_pk'],
            'courslet_pk': self.kwargs['courslet_pk'],
            'pk': self.object.id
        })

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object:
            return self.render(
                'ctms/error.html',

            )
        form = self.get_form()
        answer_form = CreateEditUnitAnswerForm(**self.get_answer_form_kwargs())
        formset = self.get_formset()

        answer_required = self.request.POST['unit_type'] == Lesson.ORCT_QUESTION
        if answer_required:
            answer_form_is_valid = answer_form.is_valid()

        has_error = False

        if form.is_valid():
            self.form_valid(form)
            if answer_required:
                if answer_form_is_valid:
                    answer_form.save(self.object.unit, self.request.user, self.object)
                else:
                    has_error = True
                    messages.add_message(request, messages.WARNING, "Please correct error in answer")

                if formset.is_valid():
                    messages.add_message(request, messages.SUCCESS, "Unit successfully updated")
                    self.formset_valid(formset)
                else:
                    has_error = True
                    self.formset_invalid(formset)
            else:
                messages.add_message(request, messages.SUCCESS, "Unit successfully updated")
        else:
            has_error = True
            messages.add_message(request, messages.WARNING, "Please correct errors below")

        if not has_error:
            cache.delete(memoize.cache_key('get_units_by_courselet', self.get_courslet()))
            return HttpResponseRedirect(self.get_success_url())

        context = {
            'course': self.get_course(),
            'courslet': self.get_courslet(),
            'unit': self.object,
            'errors_formset': formset,
            'form': form,
            'answer_form': answer_form,
        }
        context.update(self.kwargs)
        return self.render_to_response(context)

    def formset_invalid(self, formset):
        messages.add_message(self.request, messages.WARNING, "Please correct errors in Error Models section")

    def get_answer_form_kwargs(self):
        kwargs = {}
        ul = self.get_unit_lesson()
        answer = None
        if ul:
            answer = ul.get_answers().last()
        kwargs['initial'] = {'answer': answer.lesson.text} if answer else {}
        kwargs['instance'] = answer.lesson if answer else None
        kwargs['prefix'] = 'answer_form'

        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs

    def formset_valid(self, formset):
        """Save data to db from formset instance. NOT return any response to user."""
        ul = self.get_unit_lesson()
        dummy_concept = self.get_or_create_dummy_concept(ul)
        if not ul.lesson.concept:
            ul.lesson.concept = dummy_concept
            ul.lesson.addedBy = self.request.user

        for err_form in formset:
            # go though all forms in formset except forms which should be deleted.
            if err_form.is_valid() and err_form.cleaned_data and not err_form.cleaned_data['DELETE']:
                err_form.save(ul, self.request.user)

        if formset.deleted_forms:
            formset.save(commit=False)
            for del_form in formset.deleted_forms:
                obj = del_form.instance
                err_ul = UnitLesson.objects.filter(id=formset.lesson_ul_ids.get(obj.id)).first()
                # check that ul.id was not corrupted and has such lesson.
                if err_ul and err_ul.lesson == obj:
                    err_ul.delete()

    def get_or_create_dummy_concept(self, ul):
        if not ul.lesson.concept:
            admin = User.objects.get(username='admin')
            concept, created = Concept.objects.get_or_create(
                title='Dummy Concept',
                isError=False,
                addedBy=admin
            )
        else:
            concept = ul.lesson.concept
        return concept

    def form_valid(self, form):
        """Save data to DB."""
        form.save(commit=True)

    def get_initial(self):
        init = super(CreateEditUnitView, self).get_initial()
        ul = self.get_unit_lesson()
        if ul:
            if ul.lesson.kind not in [choice[0] for choice in self.form_class.KIND_CHOICES]:
                init['unit_type'] = self.form_class.DEFAULT_UNIT_TYPE
            else:
                init['unit_type'] = ul.lesson.kind
        return init

    def get_form_kwargs(self):
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'instance': self.get_form_initial()
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_queryset(self):
        courselet = self.get_courslet()
        return self.get_units_by_courselet(courselet)

    def get_object(self, queryset=None):
        obj = self.get_unit_lesson()
        if not obj or (obj and obj.addedBy != self.request.user):
            raise Http404()
        return obj

    def get_form_initial(self):
        ul = self.get_unit_lesson()
        if ul:
            return ul.lesson

    def get_ul_errors(self):
        ul = self.get_unit_lesson()
        if ul:
            return ul.get_errors()
        else:
            return UnitLesson.objects.none()

    def get_formset_queryset(self):
        ul_errors = self.get_ul_errors().values('lesson', 'id')
        qs = Lesson.objects.filter(id__in=[i['lesson'] for i in ul_errors])
        lesson_ul_id = {i['lesson']: i['id'] for i in ul_errors}
        for lesson in qs:
            # hack to pass ul id to form
            setattr(lesson, 'ul_id', lesson_ul_id[lesson.id])
        return qs

    def get_context_data(self, **kwargs):
        context = super(CreateEditUnitView, self).get_context_data(**kwargs)
        context.update({
            'course': self.get_course(),
            'courslet': self.get_courslet(),
            'unit': self.object,
            'errors_formset': ErrorModelFormSet(**self.get_formset_kwargs()),
            'answer_form': CreateEditUnitAnswerForm(**self.get_answer_form_kwargs()),
        })
        return context


class RedirectToCourseletPreviewView(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):
    course_pk_name = 'course_pk'

    def get(self, request, course_pk, pk):
        course = self.get_course()
        course_unit = course.courseunit_set.filter(id=pk).first()
        if course_unit:
            # create EnrollCode
            enroll = EnrollUnitCode.get_code_for_user_chat(
                course_unit=course_unit,
                is_live=False,
                user=request.user,
                is_preview=True
            )

        return redirect('chat:preview_courselet', **{'enroll_key': enroll.enrollCode})


class RedirectToAddUnitsView(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courset_pk'

    def get(self, request, course_pk, pk):
        course = self.get_course()
        course_unit = course.courseunit_set.filter(id=pk).first()

        if course_unit:
            # create EnrollCode
            enroll = EnrollUnitCode.get_code_for_user_chat(
                course_unit=course_unit,
                is_live=False,
                user=request.user,
            )
        return redirect('chat:add_units_by_chat',
                        **{'enroll_key': enroll.enrollCode, 'course_id': course.id, 'courselet_id': course_unit.id})


class InvitesListView(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Invite
    form_class = InviteForm
    course_pk_name = 'pk'
    template_name = 'ctms/invite_list.html'

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        kwargs['invites'] = Invite.objects.my_invites(request=self.request).filter(course=self.get_course())
        kwargs['invite_tester_form'] = self.form_class(initial={'type': 'tester', 'course': self.get_course()})
        course = self.get_course()
        if waffle.switch_is_active('ctms_invite_students'):
            courselet = CourseUnit.objects.filter(course=course).first()
            # We no longer need a form
            # kwargs['invite_student_form'] = self.form_class(initial={'type': 'student', 'course': self.get_course()})
            if courselet:
                kwargs['enroll_code'] = EnrollUnitCode.get_code(courselet)

        kwargs['course'] = course
        kwargs['domain'] = 'https://{0}'.format(Site.objects.get_current().domain)
        return kwargs

    def get_form_kwargs(self):
        kwargs = super(InvitesListView, self).get_form_kwargs()
        kwargs['course'] = self.get_course()
        kwargs['instructor'] = self.request.user.instructor
        return kwargs

    def get_initial(self):
        return {
            'course': self.get_course(),
        }

    def form_valid(self, form):
        # There's no longer a form on the students invitation page
        # if form.cleaned_data['type'] == 'student' and not waffle.switch_is_active('ctms_invite_students'):
        #     # if type - student and ctms_invite_students is disabled
        #     messages.add_message(
        #         self.request, messages.WARNING, "You can not send invitations to students yet"
        #     )
        #     return self.form_invalid(form)
        response = super(InvitesListView, self).form_valid(form)
        self.object.send_mail(self.request, self)
        messages.add_message(self.request, messages.SUCCESS, "Invitation successfully sent")
        return response

    def form_invalid(self, form):
        response = super(InvitesListView, self).form_invalid(form)
        messages.add_message(self.request, messages.WARNING,
                             "Invitation could not be sent because of errors listed below")
        return response


class JoinCourseView(CourseCoursletUnitMixin, View): # NewLoginRequiredMixin
    NEED_INSTRUCTOR = False

    def get(self, *args, **kwargs):
        invite = get_object_or_404(Invite, code=self.kwargs['code'])
        if self.request.user.is_authenticated():
            if invite.user and invite.user == self.request.user or invite.email == self.request.user.email:
                # if user is a person for whom this invite
                if invite.type == 'tester':
                    messages.add_message(self.request, messages.SUCCESS,
                                         "You just joined course as tester")
                    invite.status = 'joined'
                    invite.save()
                    return redirect(reverse('lms:tester_course_view', kwargs={'course_id': invite.course.id}))
                elif invite.type == 'student':
                    messages.add_message(self.request, messages.SUCCESS,
                                         "You just joined course as student")
                    invite.status = 'joined'
                    invite.save()
                    return redirect(reverse('lms:course_view', kwargs={'course_id': invite.course.id}))
            # if user is not owned this invite
            return HttpResponseRedirect("{}?next={}".format(reverse('new_login'), self.request.path))
        else:
            u_hash = uuid4().hex
            self.request.session['u_hash'] = u_hash
            kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
            kwargs['u_hash'] = u_hash
            kwargs['next'] = self.request.path
            invite = get_object_or_404(Invite, code=self.kwargs['code'])
            init_data = {'next': kwargs['next'], 'email': invite.email, 'u_hash': kwargs['u_hash']}
            if invite.user:
                # user already registered
                # show login page
                kwargs['form'] = EmailLoginForm(initial=init_data)
                template_name = 'psa/new_custom_login.html'
            else:
                # user not yet registered
                # show signup page
                # try to find user with email
                user = invite.search_user_by_email(invite.email)
                if user:
                    invite.user = user
                    invite.save()
                    kwargs['form'] = EmailLoginForm(initial=init_data)
                    template_name = 'psa/new_custom_login.html'
                else:
                    kwargs['form'] = SignUpForm(initial=init_data)
                    template_name = 'psa/signup.html'
            return self.render(template_name, kwargs)


class ResendInviteView(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):
    def post(self, request, code):
        invite = get_object_or_404(Invite, code=code)
        if invite.course.addedBy != self.request.user:
            raise Http404()
        response = invite.send_mail(self.request, self)
        messages.add_message(self.request, messages.SUCCESS,
                             "We just resent invitation to {}".format(invite.email))
        return json_response(response)


class DeleteInviteView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    query_pk_and_slug = True
    slug_url_kwarg = 'code'
    slug_field = 'code'
    pk_url_kwarg = 'pk'
    model = Invite

    def get_queryset(self, queryset=None):
        if queryset:
            return queryset.my_invitest(self.request)
        return Invite.objects.my_invites(self.request)

    def get_success_url(self):
        return reverse('ctms:course_invite', kwargs={'pk': self.get_object().course.id})

    def delete(self, request, *args, **kwargs):
        response = super(DeleteInviteView, self).delete(request, *args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, "Invite successfully deleted")
        return response


class EmailSentView(TemplateView):  # NewLoginRequiredMixin , CourseCoursletUnitMixin ?
    template_name = 'ctms/email_sent.html'

    def get_context_data(self, **kwargs):
        kw = super(EmailSentView, self).get_context_data(**kwargs)
        kw.update({'resend_user_email': self.request.session.get('resend_user_email')})
        return kw


class ReorderUnits(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):
    def post(self, request, course_pk, courslet_pk):
        # new ordered ids are in request.POST['ordered_ids']
        data = json.loads(request.POST.get('data') or '{}')
        ids = [int(i) for i in data.get('ordered_ids')]

        if not ids:
            return JsonResponse({'ok': 0, 'err': 'empty'})

        order = range(len(ids))
        id_order = dict(zip(ids, order))
        # check that all ids are unique
        if len(set(ids)) != len(ids):
            raise JsonResponse({'ok': 0, 'err': 'not uniq'})

        courselet = self.get_courslet()
        units = self.get_units_by_courselet(courselet)

        old_ids = units.values_list('id', flat=True)
        old_order = units.values_list('order', flat=True)
        old_id_order = dict(zip(old_ids, old_order))

        # check that all provided ids are correct
        for _id in ids:
            if _id not in old_ids:
                raise JsonResponse({'ok': 0, 'err': 'not correct ids'})

        for unit in units:
            _id = unit.id
            order = id_order[_id]
            if old_id_order[_id] == order:
                continue
            unit.order = order
            unit.save()
        cache.delete(memoize.cache_key('get_units_by_courselet', courselet))
        return JsonResponse({'ok': 1, 'msg': 'Order has been changed!'})


class Onboarding(NewLoginRequiredMixin, TemplateView):
    template_name = 'ctms/onboarding.html'

    def get_context_data(self, **kwargs):
        context = super(Onboarding, self).get_context_data(**kwargs)
        users_course = Course.objects.filter(addedBy=self.request.user).last()
        users_courselet = Unit.objects.filter(addedBy=self.request.user).last()
        users_thread = Lesson.objects.filter(addedBy=self.request.user).last()
        introduction_course_id = get_onboarding_setting(onboarding.INTRODUCTION_COURSE_ID)
        course = Course.objects.filter(id=introduction_course_id).first()
        course_unit = course.courseunit_set.all().first()
        enroll_unit_code = course_unit.enrollunitcode_set.all().first()
        enroll_url = '/chat/enrollcode/{}'.format(enroll_unit_code.get_code(course_unit))
        context.update(dict(
            introduction_course=course,
            users_course=users_course,
            users_courselet=users_courselet,
            users_thread=users_thread,
            enroll_url=enroll_url
        ))
        status = c_onboarding_status(use_secondary=True).find_one({'user_id': self.request.user.id}) or {}
        steps = [(key, status.get(key, False)) for key in get_onboarding_steps()]
        context.update({
            'steps': steps,
        })
        return context
