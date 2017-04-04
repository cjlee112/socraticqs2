from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.db import models

from chat.models import EnrollUnitCode

from ct.models import Course, CourseUnit, Unit, UnitLesson, Lesson, Response, Role, Concept
from ctms.forms import (
    CourseForm,
    CreateCourseletForm,
    EditUnitForm,
    AddEditUnitForm,
    ErrorModelFormSet,
    AddEditUnitAnswerForm
)
from ct.models import Course, CourseUnit, Unit, UnitLesson, Lesson, Response
from ctms.forms import CourseForm, CreateCourseletForm, EditUnitForm, InviteForm
from ctms.models import Invite
from mysite.mixins import NewLoginRequiredMixin


class CourseCoursletUnitMixin(object):
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'
    response_class = TemplateResponse

    def render(self, template_name, context):
        return self.response_class(
            request=self.request,
            template=template_name,
            context=context,
        )

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
            models.Q(addedBy=self.request.user) | (
             models.Q(invite__user=self.request.user) |
             models.Q(invite__email=self.request.user.email)
            ) |
            models.Q(role__role=Role.INSTRUCTOR, role__user=self.request.user)
        ).distinct()

    def get_my_or_shared_with_me_course_units(self):
        return CourseUnit.objects.filter(
            models.Q(addedBy=self.request.user) | (
             models.Q(course__invite__user=self.request.user) |
             models.Q(course__invite__email=self.request.user.email)
            ) |
            models.Q(course__role__role=Role.INSTRUCTOR, course__role__user=self.request.user) |
            models.Q(course__addedBy=self.request.user)
        ).distinct()

    def get_courselets_by_course(self, course):
        return course.courseunit_set.filter(order__isnull=False)

    def get_units_by_courselet(self, courselet):
        # UnitLesson
        return courselet.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by(
            'order'
        ).annotate(
            responses_count=models.Count('response')
        )

    def get_invite_by_code_request_or_404(self, code):
        return get_object_or_404(
            Invite,
            models.Q(user__email=self.request.user.email) |
            models.Q(email=self.request.user.email),
            code=code
        )

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

    def get_formset_prefix(self):
        """
        Returns the prefix to use for forms on this view
        """
        return self.formset_prefix

    def get_formset_kwargs(self):
        kwargs = {
            'initial': self.get_formset_initial(),
            # 'prefix': self.get_formset_prefix(),
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
        my_courses = Course.objects.filter(
            models.Q(addedBy=self.request.user)  # |
        )
        shared_courses = [invite.course for invite in self.request.user.invite_set.all()]
        courses_shared_by_role = Course.objects.filter(role__role=Role.INSTRUCTOR, role__user=self.request.user)
        course_form = None
        if not my_courses and not shared_courses:
            course_form = CourseForm()

        return {
            'my_courses': my_courses,
            'shared_courses': shared_courses,
            'course_form': course_form,
            'instructor_role_courses': courses_shared_by_role

        }

    def post(self, request):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.addedBy = request.user
            course.save()
            return redirect(reverse('ctms:course_view', kwargs={'course_id': course.id}))
        return render(
            request,
            'ctms/my_courses.html',
            {'course_form': form}
        )


class CreateCourseView(NewLoginRequiredMixin, CreateView):
    template_name = 'ctms/my_courses.html'
    model = Course
    fields = ['title']
    # form_class = CourseForm

    def form_valid(self, form):
        form.instance.addedBy = self.request.user
        self.object = form.save()
        return redirect(reverse('ctms:course_view', kwargs={'pk': self.object.id}))


class UpdateCourseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    template_name = 'ctms/course_form.html'
    model = Course
    fields = ['title']

    def get_object(self, queryset=None):
        if 'pk' in self.kwargs:
            return Course.objects.filter(
                models.Q(id=self.kwargs.get('pk')) &
                (
                    models.Q(addedBy=self.request.user) | (
                        models.Q(invite__user=self.request.user) |
                        models.Q(invite__email=self.request.user.email)
                    ) |
                    models.Q(role__role=Role.INSTRUCTOR, role__user=self.request.user)
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


class SharedCoursesListView(NewLoginRequiredMixin, ListView):
    context_object_name = 'shared_courses'
    template_name = 'ctms/sharedcourse_list.html'
    model = Invite
    queryset = Invite.objects.all()

    def get_queryset(self):
        qs = super(SharedCoursesListView, self).get_queryset()
        q = qs.shared_for_me(self.request)
        print "Shared for me ", q
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


class UnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    template_name = 'ctms/unit_detail.html'
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


class CreateUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
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
            }
        )

    def form_valid(self, form):
        courslet = self.get_courslet()
        unit = courslet.unit

        self.object = unit.create_lesson(
            title=form.cleaned_data['title'], text='', author=self.request.user
        )
        # create UnitLesson with blank answer for this unit
        unit_lesson = UnitLesson.create_from_lesson(self.object, unit, order='APPEND', addAnswer=True)

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


class ResponseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = Response
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'unit_pk'
    template_name = 'ctms/response_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        return kwargs


class CoursletSettingsView(NewLoginRequiredMixin, CourseCoursletUnitMixin, UpdateView):
    model = Unit
    fields = ('title',)
    course_pk_name = 'course_pk'
    courslet_pk_name = 'pk'
    template_name = 'ctms/courslet_settings.html'

    def get_object(self, queryset=None):
        if queryset:
            return queryset.get(pk=self.kwargs.get('pk')).unit
        else:
            return self.get_my_or_shared_with_me_courses().get(pk=self.kwargs.get('pk')).unit

    def get_success_url(self):
        return reverse('ctms:courslet_view', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'course': self.get_course(),
            'courslet': self.get_courslet(),
        })
        return kwargs


class CoursletDeleteView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
    model = CourseUnit
    template_name = 'ctms/courselet_confirm_delete.html'

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


class DeleteUnitView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DeleteView):
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


class UnitSettingsView(NewLoginRequiredMixin, CourseCoursletUnitMixin, DetailView):
    model = UnitLesson
    course_pk_name = 'course_pk'
    courslet_pk_name = 'courslet_pk'
    unit_pk_name = 'pk'
    template_name = 'ctms/unit_settings.html'

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



class AddUnitEditView(NewLoginRequiredMixin, CourseCoursletUnitMixin, FormSetBaseView, UpdateView):
    model = Lesson
    form_class = AddEditUnitForm
    formset_class = ErrorModelFormSet
    unit_pk_name = 'pk'
    template_name = 'ctms/unit_edit.html'
    HANDLE_FORMSET = True

    def get_success_url(self):
        return reverse('ctms:courslet_view', kwargs={
            'course_pk': self.kwargs['course_pk'],
            'pk': self.kwargs['courslet_pk'],
        })

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        answer_form = AddEditUnitAnswerForm(**self.get_answer_form_kwargs())

        formset = self.get_formset()
        if form.is_valid():
            if answer_form.is_valid():
                answer = answer_form.save(self.object.unit, self.request.user, self.object)

            response = self.form_valid(form)

            if not self.HANDLE_FORMSET:
                return response
            if self.object.lesson.kind == Lesson.ORCT_QUESTION and formset.is_valid():
                return self.formset_valid(formset)
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

    def get_answer_form_kwargs(self):
        ul = self.get_unit_lesson()
        answer = ul.get_answers().last()
        kwargs = {}
        kwargs['initial'] = {'answer': answer.lesson.text} if answer else {}
        kwargs['instance'] = answer.lesson if answer else None
        kwargs['prefix'] = 'answer_form'

        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs

    def formset_valid(self, formset):
        error_models = []
        ul = self.get_unit_lesson()
        dummy_concept = self.get_or_create_dummy_concept(ul)
        if not ul.lesson.concept:
            ul.lesson.concept = dummy_concept
            ul.lesson.addedBy = self.request.user
            ul.lesson.save_root(dummy_concept, Lesson.ANSWER)
        for err_form in formset:
            error_models.append(err_form.save(ul, self.request.user))
        return HttpResponseRedirect(self.get_success_url())

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
        form.save(commit=True)
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        init = super(AddUnitEditView, self).get_initial()
        ul = self.get_unit_lesson()
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
        if queryset:
            return queryset.filter(id=self.kwargs.get(self.unit_pk_name)).first()
        else:
            return self.get_unit_lesson()

    def get_form_initial(self):
        ul = self.get_unit_lesson()
        return ul.lesson

    def get_formset_initial(self):
        lessons = [
            {
                'title': q.lesson.title,
                'text': q.lesson.text
            }
            for q in self.get_unit_lesson().get_errors()
        ]
        return lessons

    def get_context_data(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs.update({
            'course': self.get_course(),
            'courslet': self.get_courslet(),
            'unit': self.object,
            'errors_formset': ErrorModelFormSet(**self.get_formset_kwargs()),
            'answer_form': AddEditUnitAnswerForm(**self.get_answer_form_kwargs()),
        })
        return kwargs


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


class SendInvite(NewLoginRequiredMixin, CourseCoursletUnitMixin, CreateView):
    model = Invite
    form_class = InviteForm
    course_pk_name = 'pk'
    template_name = 'ctms/invite_list.html'

    def get_context_data(self, **kwargs):
        kwargs['tester_invites'] = Invite.testers.my_invites(self.request)
        kwargs['student_invites'] = Invite.students.my_invites(self.request)
        return kwargs

    def get_form_kwargs(self):
        kwargs = super(SendInvite, self).get_form_kwargs()
        # kwargs['']
        return kwargs

    def get_initial(self):
        return {
            'course': self.get_course(),
        }


class InvitesListView(NewLoginRequiredMixin, CourseCoursletUnitMixin, TemplateView):
    model = Invite
    form_class = InviteForm
    course_pk_name = 'pk'
    template_name = 'ctms/invite_list.html'

    def get_context_data(self, **kwargs):
        kwargs['invites'] = Invite.objects.my_invites(request=self.request).filter(course=self.get_course())
        kwargs['invite_tester_form'] = self.form_class(initial={'type': 'tester', 'course': self.get_course()})
        kwargs['invite_student_form'] = self.form_class(initial={'type': 'student', 'course': self.get_course()})
        return kwargs

    def post(self, *args, **kwargs):
        form = self.form_class(self.get_course(), self.request.user.instructor, data=self.request.POST)
        if form.is_valid():
            invite = form.save()
            response = invite.send_mail(self.request, self)
            return response
        return render(
            self.request,
            self.template_name,
            self.get_context_data()
        )


class TesterJoinCourseView(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):

    def get(self, *args, **kwargs):
        invite = self.get_invite_by_code_request_or_404(code=self.kwargs['code'])
        invite.status = 'joined'
        invite.save()
        if invite.type == 'tester':
            return redirect(reverse('lms:tester_course_view', kwargs={'course_id': invite.course.id}))
        elif invite.type == 'student':
            return redirect(reverse('lms:course_view', kwargs={'course_id': invite.course.id}))
        else:
            raise Http404()


class ResendInviteView(NewLoginRequiredMixin, CourseCoursletUnitMixin, View):
    def post(self, request, code):
        invite = self.get_invite_by_code_request_or_404(code=code)
        response = invite.send_mail(self.request, self)
        return response


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
        return reverse('ctms:share_course', kwargs={'pk': self.get_object().course.id})
