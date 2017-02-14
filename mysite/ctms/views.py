from django.http.response import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.db import models
from ct.models import Course, CourseUnit, Unit, UnitLesson, Lesson, Response
from ctms.forms import CourseForm, CourseUnitForm, CreateCoursletForm, CreateUnitForm, EditUnitForm  #, CreateUnitForm
from ctms.models import SharedCourse
from mysite.mixins import LoginRequiredMixin


class CourseCoursletUnitMixin(object):
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'

    def get_course(self):
        return Course.objects.filter(id=self.kwargs.get(self.course_pk_name)).first()

    def get_courslet(self):
        return CourseUnit.objects.filter(id=self.kwargs.get(self.courslet_pk_name)).first()

    def get_unit_lesson(self):
        return UnitLesson.objects.filter(id=self.kwargs.get(self.unit_pk_name)).first()

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        return kwargs

    def get_my_or_shared_with_me_courses(self):
        return Course.objects.filter(
            models.Q(addedBy=self.request.user) |
            models.Q(shared_courses__to_user=self.request.user)
        ).distinct()

    def get_my_or_shared_with_me_course_units(self):
        # UnitLesson
        return CourseUnit.objects.filter(
            models.Q(addedBy=self.request.user) |
            models.Q(course__shared_courses__to_user=self.request.user)
        ).distinct()

class MyCoursesView(LoginRequiredMixin, CourseCoursletUnitMixin, View):
    def get(self, request):
        my_courses = Course.objects.filter(
            models.Q(addedBy=self.request.user) # |
            # models.Q(shared_courses__to_user=self.request.user)
        )
        shared_courses = SharedCourse.objects.filter(to_user=request.user)
        course_form = None
        if not my_courses and not shared_courses:
            course_form = CourseForm()
        return render(
            request,
            'ctms/my_courses.html',
            {'my_courses': my_courses,
             'shared_courses': shared_courses,
             'course_form': course_form,
            }
        )

    def post(self, request):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.addedBy = request.user
            course.save()
            return redirect(reverse('lms:course_view', kwargs={'course_id': course.id}))
        return render(
            request,
            'ctms/my_courses.html',
            {'course_form': form}
        )

class CreateCourseView(LoginRequiredMixin, CreateView):
    template_name = 'ctms/my_courses.html'
    model = Course
    fields = ['title']
    # form_class = CourseForm

    def form_valid(self, form):
        form.instance.addedBy = self.request.user
        self.object = form.save()
        return redirect(reverse('ctms:course_view', kwargs={'pk': self.object.id}))


class UpdateCourseView(LoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    template_name = 'ctms/course_form.html'
    model = Course
    fields = ['title']

    def get_object(self, queryset=None):
        if 'pk' in self.kwargs:
            return Course.objects.filter(
                models.Q(id=self.kwargs.get('pk')) &
                (
                    models.Q(addedBy=self.request.user) |
                    models.Q(shared_courses__to_user=self.request.user)
                )
            ).distinct().first()

    def form_valid(self, form):
        form.instance.addedBy = self.request.user
        return super(UpdateCourseView, self).form_valid(form)

    def get_success_url(self):
        return reverse('ctms:course_view', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs['object'] = self.object
        return kwargs

class DeleteCourseView(LoginRequiredMixin, DeleteView):
    model = Course
    
    def get_queryset(self):
        return Course.objects.filter(addedBy=self.request.user)

    def get_success_url(self):
        return reverse('ctms:my_courses')


class SharedCoursesListView(LoginRequiredMixin, ListView):
    context_object_name = 'shared_courses'
    model = SharedCourse

    def get_queryset(self):
        qs = super(SharedCoursesListView, self).get_queryset()
        return qs.filter(to_user=self.request.user)


class CourseView(LoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
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


class CoursletView(LoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = CourseUnit
    template_name = 'ctms/courseunit_detail.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'pk'
    unit_pk_name = None

    def get_queryset(self):
        # UnitLesson
        return self.get_my_or_shared_with_me_course_units()

    def get_context_data(self, **kwargs):
        kwargs.update({
            'u_lessons': self.object.unit.unitlesson_set.filter(
                kind=UnitLesson.COMPONENT,
                order__isnull=False
            ).order_by(
                'order'
            ).annotate(
                responses_count=models.Count('response')
            ),
            # 'course_pk': self.kwargs['course_pk'],
            # 'courslet_pk': self.kwargs['pk'],
        })
        kwargs.update(self.kwargs)
        return kwargs


class CreateCoursletView(LoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Unit
    template_name = 'ctms/unit_form.html'
    fields = ('title',)
    form = CreateCoursletForm

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
        kwargs.update(self.kwargs)
        kwargs.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return kwargs


class UnitView(LoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    template_name = 'ctms/unitlesson_detail.html'
    model = UnitLesson

    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'

    def get_context_data(self, **kwargs):
        super(UnitView, self).get_context_data(**kwargs)
        course = self.get_course()
        courslet = self.get_courslet()
        kwargs.update({
            'course': course,
            'courslet': courslet,
            'responses': self.object.response_set.all(),
        })
        kwargs.update(self.kwargs)
        return kwargs


class CreateUnitView(LoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Lesson
    fields = ('title',)
    template_name = 'ctms/unit_form.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'

    def get_success_url(self):
        return reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_course().id,
                'courslet_pk': self.get_courslet().id,
                'pk': self.object.unit_lesson.id
        })

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.addedBy = self.request.user
        self.object.save()
        courslet = self.get_courslet()
        unit = courslet.unit
        unit_lesson = UnitLesson.objects.create(
            unit=unit,
            order=0,
            lesson=self.object,
            addedBy=self.request.user,
            treeID=self.object.id,
        )
        self.object.unit_lesson = unit_lesson
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return kwargs


class EditUnitView(LoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    model = UnitLesson
    template_name = 'ctms/unit_form.html'
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'
    form_class = EditUnitForm

    def get_object(self, queryset=None):
        return self.get_unit_lesson().lesson

    def get_success_url(self):
        return reverse('ctms:unit_view', kwargs=self.kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=True)
        # self.object.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return kwargs


class ResponseView(LoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = Response
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'
    template_name = 'ctms/response_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        return kwargs


class CoursletSettingsView(LoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    model = Unit
    fields = ('title',)
    course_pk_name = 'course_pk'
    courslet_pk_name = 'pk'
    template_name = 'ctms/courslet_settings.html'

    def get_object(self, queryset=None):
        return get_object_or_404(CourseUnit, pk=self.kwargs.get('pk')).unit

    def get_success_url(self):
        return reverse('ctms:courslet_view', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'course': self.get_course(),
            'courslet': self.get_courslet(),
        })
        return kwargs


class CoursletDeleteView(LoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    model = CourseUnit
    def get_success_url(self):
        course = self.get_course()
        if course:
            return reverse('ctms:course_view', kwargs={'pk': course.id})
        return reverse('ctms:my_courses')


class DeleteUnitView(LoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    model = UnitLesson

    def get_success_url(self):
        course = self.get_course()
        courslet = self.get_courslet()
        if course and courslet:
            return reverse('ctms:courslet_view', kwargs={
                'course_pk': course.id,
                'pk': courslet.id
            })
        return reverse('ctms:my_courses')


class UnitSettingsView(LoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = UnitLesson
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'
    template_name = 'ctms/unitlesson_settings.html'

    def get_object(self, queryset=None):
        return self.get_unit_lesson().lesson

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'unit_lesson': self.get_unit_lesson(),
            'course': self.get_course(),
            'courslet': self.get_courslet()
        })
        return kwargs
