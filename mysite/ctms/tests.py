from ddt import ddt, data, unpack
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from django.db import models

from ct.models import Unit, Course, CourseUnit, Lesson, UnitLesson, Response, NEED_HELP_STATUS
from ctms.forms import EditUnitForm
from ctms.models import Invite


class MyTestCase(TestCase):
    models_to_check = tuple()
    context_should_contain_keys = tuple()

    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

        self.user2 = User.objects.create_user('test1', 'test1@test.com', 'test')

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit.save()
        self.lesson = Lesson(title='title', text='text', addedBy=self.user)
        self.lesson.save()
        self.unitlesson = UnitLesson(
            unit=self.unit, order=0,
            lesson=self.lesson, addedBy=self.user,
            treeID=self.lesson.id
        )
        self.unitlesson.save()


        resp1 = Response(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
            text="Some text user may respond",
            author=self.user,
            status=NEED_HELP_STATUS,
            selfeval=Response.DIFFERENT
        )
        resp1.save()

        resp2 = Response(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
            text="Some text user may be responded 2",
            author=self.user,
            status=NEED_HELP_STATUS,
            selfeval=Response.DIFFERENT
        )
        resp2.save()

        self.client.login(username=self.username, password=self.password)
        self.url = reverse('ctms:course_settings', kwargs={'pk': self.course.id})

    def get_page(self):
        return self.client.get(self.url)

    def post_data(self, data={'name': 'some test name'}):
        response = self.client.post(self.url, data, follow=True)
        return response

    def post_valid_data(self, data={'name': 'some test name'}):
        response = self.client.post(self.url, data, follow=True)
        return response

    def post_invalid_data(self, data={'name': ''}):
        response = self.client.post(self.url, data, follow=True)
        return response

    def get_my_courses(self):
        return Course.objects.filter(addedBy=self.user)

    def get_test_course(self):
        return Course.objects.get(id=self.course.id)

    def get_test_unitlessons(self):
        return self.courseunit.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by('order').annotate(
            responses_count=models.Count('response')
        )

    def get_test_unitlesson(self):
        return self.courseunit.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by('order').annotate(
            responses_count=models.Count('response')
        )[0]

    get_test_courslet = get_test_unitlesson

    get_test_response = lambda self: self.get_test_responses()[0]

    def get_test_courseunit(self):
        return CourseUnit.objects.get(id=self.courseunit.id)

    def get_test_responses(self):
        return Response.objects.filter(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
        )

    def get_model_counts(self, **kwargs):
        if isinstance(self.models_to_check, (list, tuple)):
            return {model: model.objects.filter().count()
             for model in self.models_to_check}
        return {self.models_to_check: self.models_to_check.objects.filter().count()}

    def validate_model_counts(self, first_counts, second_counts, must_equal=False):
        if isinstance(self.models_to_check, (list, tuple)):
            all_models = self.models_to_check
        else:
            all_models = [self.models_to_check]

        for model in all_models:
            if must_equal:
                self.assertEqual(first_counts[model], second_counts[model])
            else:
                self.assertNotEqual(first_counts[model], second_counts[model])

    def check_context_keys(self, response):
        for key in self.context_should_contain_keys:
            self.assertIn(key, response.context)


class MyCoursesTests(MyTestCase):
    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

        self.user2 = User.objects.create_user('test1', 'test1@test.com', 'test')

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit.save()
        self.lesson = Lesson(title='title', text='text', addedBy=self.user)
        self.lesson.save()
        self.unitlesson = UnitLesson(
            unit=self.unit, order=0,
            lesson=self.lesson, addedBy=self.user,
            treeID=self.lesson.id
        )
        self.unitlesson.save()
        self.client.login(username=self.username, password=self.password)
        self.url = reverse('ctms:my_courses')

    def get_my_courses_page_test(self):
        response = self.client.get(self.url)
        # should contain 1 course
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertIn(self.course, response.context['my_courses'])
        self.assertFalse(response.context['shared_courses'])

    def my_courses_show_shared_courses_test(self):
        self.course.addedBy = self.user2
        self.course.save()
        # create shared course
        shared_course = Invite.create_new(True, self.course, self.user2, self.user.email, 'tester')
        response = self.client.get(self.url)
        # should return shared courses
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertFalse(self.course in response.context['my_courses'])
        self.assertTrue(shared_course in response.context['shared_courses'])

    def my_courses_show_create_course_form(self):
        self.course.delete()
        response = self.client.get(self.url)
        # should return Course form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertFalse(len(response.context['my_courses']) < 0)

    def post_valid_create_course_form(self):
        courses_cnt = Course.objects.filter(addedBy=self.user).count()
        course_ids = [
            i['id'] for i in
            Course.objects.filter(addedBy=self.user).values('id')
        ]
        data = {
            'name': 'some course'
        }
        response = self.client.post(self.url, data)
        new_courses = Course.objects.filter(addedBy=self.user)
        new_course = new_courses.exclude(id__in=course_ids).get()
        self.assertEqual(new_courses.count(), courses_cnt)
        self.assertRedirects(response, reverse('ctms:course_view', kwargs={'course_id': new_course.id}))
        return response

    def post_invalid_create_course_form(self):
        courses_cnt = Course.objects.filter(addedBy=self.user).count()
        course_ids = [
            i['id'] for i in
            Course.objects.filter(addedBy=self.user).values('id')
        ]
        data = {
            'name': ''
        }
        response = self.client.post(self.url, data)
        new_courses = Course.objects.filter(addedBy=self.user)
        new_course = new_courses.exclude(id__in=course_ids)
        self.assertNotEqual(new_courses.count(), courses_cnt)
        # course was not created
        self.assertEqual(len(new_course) == 0)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        return response

    def post_valid_create_course_form_to_create_course_view(self):
        self.url = reverse('ctms:create_course')
        self.post_valid_create_course_form()

    def post_invalid_create_course_form_to_create_course_view(self):
        self.url = reverse('ctms:create_course')
        response = self.post_invalid_create_course_form()


class UpdateCourseViewTests(MyTestCase):
    def post_valid_update_course_form(self):
        cnt = self.get_my_courses().count()
        response = self.post_valid_create_course_form()
        # check that courses count doesn't change
        self.assertEqual(cnt, self.get_my_courses().count())
        # check that name has been changed
        self.assertEqual(self.get_test_course().name, 'some test name')
        self.assertRedirects(response, reverse('ctms:course_view', kwargs={'pk': self.course.id}))

    def post_invalid_update_course_form(self):
        cnt = self.get_my_courses().count()
        response = self.post_invalid_data()
        self.assertEqual(cnt, self.get_my_courses().count())
        self.assertEqual(response.context['object'], self.get_test_course())
        self.assertTemplateNotUsed(response, 'ctms/my_courses.html')


class DeleteCourseViewTest(MyTestCase):
    def setUp(self):
        super(DeleteCourseViewTest, self).setUp()
        self.url = reverse('ctms:course_delete', kwargs={'pk': self.course.id})

    def post_success(self):
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertNotEqual(cnt, self.get_my_courses().count())
        self.assertRedirects(response, reverse('ctms:my_courses'))

    def anonymous_post(self):
        self.client.logout()
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def delete_not_mine_course(self):
        self.course.addedBy = self.user2
        self.course.save()
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def delete_not_exist_pk_test(self):
        self.url = reverse('ctms:course_delete', kwargs={'pk': 9999999})
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)


class SharedCoursesListViewTests(MyTestCase):
    def setUp(self):
        super(SharedCoursesListViewTests, self).setUp()
        self.shared_course = SharedCourse.objects.create(
            from_user=self.user2,
            to_user=self.user,
            course=self.course
        )
        self.url = reverse('ctms:shared_courses')

    def shared_courses_list_test(self):
        response = self.client.get(self.url)
        self.assertIn(self.shared_course, response.context['shared_courses'])


class CourseViewTests(MyTestCase):
    def setUp(self):
        super(CourseViewTests, self).setUp()
        self.url = reverse('ctms:course_view', kwargs={'pk': self.course.id})

    def course_view_test(self):
        response = self.get_page()
        self.assertEqual(self.course, response.context['object'])
        self.assertEqual(
            self.course.get_course_units(publishedOnly=False),
            response.context['courslets']
        )

    def get_not_mine_course_test(self):
        self.url = reverse('ctms:course_view', kwargs={'pk': 99999})
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def logged_out_user_get_course(self):
        self.client.logout()
        response = self.get_page()
        self.assertRedirects(response, reverse('login'))


class CoursletViewTests(MyTestCase):
    def setUp(self):
        super(CoursletViewTests, self).setUp()
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': self.courseunit.id

            })

    def get_courslet_view_test(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        u_ids = [i['id'] for i in response.context['u_lessons'].values('id')]
        test_ids = [i['id'] for i in self.get_test_unitlessons().values('id')]
        self.assertEqual(u_ids, test_ids)
        self.assertIn(self.unitlesson, response.context['u_lessons'])
        self.assertEqual(self.get_test_courseunit(), response.context['object'])

    def get_courslet_view_wrong_courslet_id_test(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': 99999

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def get_courslet_view_wrong_course_id_test(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': 999999,
                'pk': self.courseunit.id

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def get_courslet_view_logged_out_user_test(self):
        self.client.logout()
        response = self.get_page()
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)


class CreateCoursletViewTests(MyTestCase):
    def setUp(self):
        super(CreateCoursletViewTests, self).setUp()
        self.url = reverse(
            'ctms:courslet_create', kwargs={
                'course_pk': self.course.id,
        })

    def post_valid_data_test(self):
        courslets_in_course = CourseUnit.objects.filter(
            course=self.course
        ).count()
        data = {'title': 'Some new Courslet'}
        response = self.post_valid_data(data)
        new_unit = CourseUnit.objects.filter(
            course=self.course
        ).count()
        self.assertNotEqual(courslets_in_course, new_unit)
        self.assertRedirects(response, reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.get_test_course().pk,
                'pk': CourseUnit.objects.all().last().id
            }
        ))


    def post_invalid_data_test(self):
        courslets_in_course = Unit.objects.filter(
            courseunit__course=self.course
        )
        data = {'title': ''}
        response = self.post_invalid_data(data)
        self.assertNotEqual(
            courslets_in_course,
            Unit.objects.filter(courseunit__course=self.course)
        )
        self.assertTemplateUsed('ctms/unit_form.html')
        self.assertIn('form', response.context)
        self.assertIn('unit_lesson', response.context)
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)


class UnitViewTests(MyTestCase):
    def get_page_test(self):
        self.url = reverse(
            'ctms:unit_view', kwargs={
                'course_pk': self.course.id,
                'courslet_pk': self.courseunit.id,
                'pk': self.unitlesson.id
            }
        )
        response = self.get_page()
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('responses', response.context)
        self.assertEqual(response.context['course'], self.course)
        self.assertEqual(response.context['courslet'], self.courseunit)
        self.assertEqual(
            list(response.context['responses'].order_by('id')),
            list(self.get_test_responses().order_by('id')),
        )


class CreateUnitViewTests(MyTestCase):
    def setUp(self):
        super(CreateUnitViewTests, self).setUp()
        self.url = reverse(
            'ctms:unit_create',
            kwargs={
                'course_pk': self.course.id,
                'courslet_pk': self.courseunit.id,

            }
        )

    def get_page_test(self):
        response = self.get_page()
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('unit_lesson', response.context)
        self.assertEqual(response.context['course'], self.course)
        self.assertEqual(response.context['courslet'], self.courseunit)
        self.assertIsNone(response.context['unit_lesson'])

    def post_valid_data_test(self):
        data = {
            'title': 'Some new new one title'
        }
        lessons_cnt = Lesson.objects.filter().count()
        unit_lsn_cnt = UnitLesson.objects.filter().count()
        response = self.post_valid_data(data)
        new_lessons_cnt = Lesson.objects.filter().count()
        new_unit_lsn_cnt = UnitLesson.objects.filter().count()
        last_ul = UnitLesson.objects.all().order_by('id').last()
        success_url = reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courslet_pk': self.get_test_courseunit().id,
                'pk': last_ul.id
        })
        self.assertRedirects(response, success_url)
        self.assertNotEqual(lessons_cnt, new_lessons_cnt)
        self.assertNotEqual(unit_lsn_cnt, new_unit_lsn_cnt)

    def post_invalid_data_test(self):
        data = {
            'title': ''
        }
        lessons_cnt = Lesson.objects.filter().count()
        unit_lsn_cnt = UnitLesson.objects.filter().count()
        response = self.post_valid_data(data)
        self.assertTemplateUsed('ctms/unit_form.html')
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('form', response.context)
        self.assertIsNone(response.context['unit_lesson'])
        self.assertEqual(lessons_cnt, Lesson.objects.filter().count())
        self.assertEqual(unit_lsn_cnt, UnitLesson.objects.filter().count())


@ddt
class EditUnitViewTests(MyTestCase):
    
    models_to_check = (UnitLesson, Lesson)
    context_should_contain_keys = ('unit_lesson', 'course', 'courslet')

    def setUp(self):
        super(EditUnitViewTests, self).setUp()
        self.pk = self.get_test_unitlessons()[0].id
        self.url = reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courslet_pk': self.get_test_courseunit().id,
                'pk': self.get_test_unitlessons()[0].id,
            }
        )

    def get_page_test(self):
        counts = self.get_model_counts()
        response = self.get_page()
        new_counts = self.get_model_counts()
        self.assertEqual(counts, new_counts)
        self.assertTemplateUsed(response, 'ctms/unit_form.html')
        self.check_context_keys(response)

    @unpack
    @data(
        (EditUnitForm.KIND_CHOICES[0][0], 'Some text is here...'),
        (EditUnitForm.KIND_CHOICES[1][0], 'Some New ORCT text is here...'),
    )
    def post_valid_data_test(self, kind, text):
        counts = self.get_model_counts()
        data = {
            'unit_type': kind,
            'text': text
        }
        response = self.post_valid_data(data)
        new_counts = self.get_model_counts()

        self.validate_model_counts(counts, new_counts, must_equal=True)
        ul = UnitLesson.objects.filter().order_by('id').last()
        url = reverse(
            'ctms:unit_view',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courslet_pk': self.get_test_courseunit().id,
                'pk': ul.id
        })
        self.assertEqual(self.get_test_unitlesson().lesson.text, text)
        self.assertEqual(self.get_test_unitlesson().lesson.kind, kind)
        self.assertRedirects(response, url)

        self.context_should_contain_keys = ('course', 'courslet', 'responses')
        self.check_context_keys(response)

    @unpack
    @data(
        # (EditUnitForm.KIND_CHOICES[0][0], ''),  # valid kind, empty text
        ('', 'Some New ORCT text is here...'),  # not valid kind, valid text
    )
    def post_invalid_data_test(self, kind, text):
        counts = self.get_model_counts()
        data = {
            'unit_type': kind,
            'text': text
        }
        response = self.post_valid_data(data)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=True)
        self.assertNotEqual(self.get_test_unitlesson().lesson.kind, kind)
        # self.assertEqual(self.get_test_unitlesson().unit.text, text)
        self.check_context_keys(response)


class ResponseViewTests(MyTestCase):
    models_to_check = (Response,)
    context_should_contain_keys = ('course_pk', 'courslet_pk', 'unit_pk', 'pk', 'object')

    def setUp(self):
        super(ResponseViewTests, self).setUp()
        self.url = reverse(
            'ctms:response_view',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courslet_pk': self.get_test_courseunit().id,
                'unit_pk': self.get_test_unitlesson().id,
                'pk': self.get_test_response().id
            }
        )

    def get_page_test(self):
        response = self.get_page()
        self.check_context_keys(response)

@ddt
class CoursletSettingsViewTests(MyTestCase):
    models_to_check = Unit
    context_should_contain_keys = ('course', 'courslet', 'form')

    def setUp(self):
        super(CoursletSettingsViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'pk': self.get_test_courseunit().id
        }
        self.url = reverse(
            'ctms:courslet_settings',
            kwargs=self.kwargs
        )

    def get_page_test(self):
        response = self.get_page()
        self.check_context_keys(response)

    @unpack
    @data(
        (True, {'title': 'SOme 111 titlee'}),
        (False, {'title': ''})
    )
    def post_data_test(self, is_valid, post_data):
        # import ipdb; ipdb.set_trace()
        counts = self.get_model_counts()
        response = self.post_valid_data(post_data)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, True)

        if is_valid:
            url = reverse('ctms:courslet_view', kwargs=self.kwargs)
            self.assertRedirects(response, url)
            self.context_should_contain_keys = ('u_lessons', 'course_pk', 'pk')

        self.check_context_keys(response)


class CoursletDeleteViewTests(MyTestCase):
    context_should_contain_keys = ('object',)
    models_to_check = CourseUnit

    def setUp(self):
        super(CoursletDeleteViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'pk': self.get_test_courslet().id
        }
        self.url = reverse('ctms:courslet_delete', kwargs=self.kwargs)

    def get_page_test(self):
        # should return delete confirmation page
        counts = self.get_model_counts()
        response = self.get_page()
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=True)
        self.assertTemplateUsed(response, 'ctms/courselet_confirm_delete.html')

    def post_page_test(self):
        counts = self.get_model_counts()
        response = self.post_valid_data(data=None)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts)
        self.assertEqual(counts[self.models_to_check], new_counts[self.models_to_check] + 1)
        self.assertRedirects(
            response,
            reverse('ctms:course_view', kwargs={'pk': self.get_test_course().id})
        )


class DeleteUnitViewTests(MyTestCase):
    context_should_contain_keys = ()
    models_to_check = UnitLesson

    def setUp(self):
        super(DeleteUnitViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'courslet_pk': self.get_test_courseunit().id,
            'pk': self.get_test_courslet().id
        }
        self.url = reverse('ctms:unit_delete', kwargs=self.kwargs)

    def delete_unit_test(self):
        counts = self.get_model_counts()
        response = self.post_valid_data()
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts)
        url = reverse('ctms:courslet_view', kwargs={
                'course_pk': self.get_test_course().id,
                'pk': self.get_test_courseunit().id
        })
        self.assertRedirects(response, url)


@ddt
class UnitSettingsViewTests(MyTestCase):
    context_should_contain_keys = ('unit_lesson', 'course', 'courslet', 'object')
    models_to_check = UnitLesson

    def setUp(self):
        super(UnitSettingsViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'courslet_pk': self.get_test_courseunit().id,
            'pk': self.get_test_unitlesson().id
        }
        self.url = reverse('ctms:unit_settings', kwargs=self.kwargs)

    def get_page_test(self):
        response = self.get_page()
        self.check_context_keys(response)

    # NOTE: may be we will need this test in future when this page will contain not only links but will update unit.
    # @unpack
    # @data(
    #     (True, {'title': "Some neeewww titleeeeee"}),
    #     (False, {'title': ""})
    # )
    # def post_data_test(self, is_valid, post_data):
    #     counts = self.get_model_counts()
    #     ul = UnitLesson.objects.get(id=self.kwargs['pk'])
    #     response = self.post_data(post_data)
    #     n_ul = UnitLesson.objects.get(id=self.kwargs['pk'])
    #     new_counts = self.get_model_counts()
    #     self.check_context_keys(response)
    #     self.validate_model_counts(counts, new_counts)
    #     if is_valid:
    #         self.assertNotEqual(n_ul.title, ul.title)
    #     else:
    #         self.assertEqual(n_ul.title, ul.title)




















