import json
import mock
import pytest

from django.urls import reverse

from pymongo.errors import ServerSelectionTimeoutError


from analytics.models import CourseReport
from api.v0.views import OnboardingBpAnalysis
from core.common.mongo import c_onboarding_status
from core.common import onboarding
from ct.models import UnitLesson, StudentError, Concept
from ctms.tests import MyTestCase


HEALTH_URL = reverse('api:v0:health-check')


def test_result_calculation(input_data):
    data, calculation, result = input_data.values()
    assert OnboardingBpAnalysis.get_result_calculation(data, calculation) == result


def test_health_positive(client, db):
    result = client.get(HEALTH_URL)

    assert result.status_code == 200
    assert 'ok' in json.loads(result.content)


def test_health_non_ok(client, db, mocker):
    """
    Ping and Stats Mongo command return non ok results.
    """
    do_health = mocker.patch('api.v0.views.do_health')
    do_health.return_value = {}, {}

    result = client.get(HEALTH_URL)

    assert result.status_code == 503


def test_health_exception(client, db, mocker):
    """
    Mongo query raises exception.
    """
    do_health = mocker.patch('api.v0.views.do_health')
    do_health.side_effect = ServerSelectionTimeoutError()

    result = client.get(HEALTH_URL)

    assert result.status_code == 503


class TestOnboardingStatus(MyTestCase):

    namespace = 'api:v0:onboarding-status'

    def setUp(self):
        super(TestOnboardingStatus, self).setUp()

        # # Hack: remove all test_ databases before test
        # for db in _conn.connector.list_databases():
        #     if 'test_' in db.get('name') and:
        #         _conn.connector.drop_database(db.get('name'))

        self.data = {
            onboarding.USER_ID: self.user.id,
            onboarding.STEP_1: False,
            onboarding.STEP_2: False,
            onboarding.STEP_3: False,
            onboarding.STEP_4: False,
        }

    def test_put_valid_data(self):

        data_to_update = {onboarding.STEP_2: True}

        c_onboarding_status().remove()

        c_onboarding_status().insert(self.data.copy())

        ensure_saved = c_onboarding_status().find_one({onboarding.USER_ID: self.user.id}, {'_id': False})

        self.assertEqual(ensure_saved, self.data)

        self.assertEqual(self.client.login(username=self.username, password=self.password), True)
        response = self.client.put(
            reverse('api:v0:onboarding-status'),
            data=json.dumps(data_to_update),
            content_type="application/json"
        )
        data = self.data.copy()
        self.assertEqual(response.status_code, 200)
        data.update(data_to_update)
        mongo_data = c_onboarding_status().find_one({onboarding.USER_ID: self.user.id}, {'_id': False})

        self.assertEqual(mongo_data, data)

    def test_put_invalid_keys(self):

        data_to_update = {'invalid_key': True}

        c_onboarding_status().remove()

        c_onboarding_status().insert(self.data.copy())

        ensure_saved = c_onboarding_status().find_one({onboarding.USER_ID: self.user.id}, {'_id': False})

        self.assertEqual(ensure_saved, self.data)

        response = self.client.put(
            reverse('api:v0:onboarding-status'),
            data=json.dumps(data_to_update),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_wo_user_403(self):
        c_onboarding_status().remove()
        self.client.logout()
        response = self.client.get(reverse(self.namespace))
        self.assertEqual(response.status_code, 403)

    def test_get_with_user_200(self):

        c_onboarding_status().remove()

        c_onboarding_status().insert(self.data.copy())

        response = self.client.get(reverse(self.namespace))
        expected_data = {
            "done": True,
        }
        response_data = json.loads(response.content)['data']
        for key in list(response_data.keys()):
            self.assertSetEqual(set(expected_data), set(response_data[key]))


class ApiAccessMixinTest(object):

    def test_permissions_instructor_allowed(self):
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

    def test_permissions_not_instructor_disallowed(self):
        self.client.login(username=self.username2, password=self.password2)
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_permissions_user_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_course_doesnt_exist(self):
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': 100}))
        self.assertEqual(response.status_code, 404)


class TestResponseViewSet(ApiAccessMixinTest, MyTestCase):

    namespace = 'api:v0:responses'

    def test_serializer_author_name(self):
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        self.assertEqual(
            json.loads(response.content)[0].get('author_name'),
            self.user.get_full_name() or self.user.username
        )


class TestErrorViewSet(ApiAccessMixinTest, MyTestCase):

    namespace = 'api:v0:errors'

    def setUp(self):
        super(TestErrorViewSet, self).setUp()
        concept = Concept(title='test title', addedBy=self.user)
        concept.save()
        self.lesson.concept = concept
        self.lesson.save()
        self.unit_lesson_error = UnitLesson(
            unit=self.unit, order=0,
            lesson=self.lesson, addedBy=self.user,
            treeID=self.lesson.id
        )
        self.unit_lesson_error.save()

        self.student_error = StudentError(
            response=self.resp1,
            errorModel=self.unit_lesson_error,
            author=self.user
        )
        self.student_error.save()

    def test_serializer_em_data(self):
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        fields_set = set([
            'id', 'lesson_concept_id', 'lesson_concept_isAbort', 'lesson_concept_isFail', 'lesson_text', 'treeID'
        ])
        em_data_set = set(json.loads(response.content)[0]['em_data'])
        self.assertSetEqual(fields_set, em_data_set)


class TestGenReportView(MyTestCase):
    namespace = 'api:v0:gen-report'

    def test_missed_course_id(self):
        response = self.client.get(reverse(self.namespace))
        self.assertEqual(response.status_code, 400)

    def test_course_doesnt_exist(self):
        response = self.client.get(reverse(self.namespace), data={'course_id': 100})
        self.assertEqual(response.status_code, 404)

    def test_not_allowed(self):
        self.client.login(username=self.username2, password=self.password2)
        response = self.client.get(reverse(self.namespace), data={'course_id': self.course.id})
        self.assertEqual(response.status_code, 403)

    @mock.patch('api.v0.views.report.delay')
    def test_report_generated(self, report):
        response = self.client.get(reverse(self.namespace), data={'course_id': self.course.id})
        self.assertEqual(response.status_code, 200)
        report.assert_called_with(str(self.course.id), self.user.id)


class TestCourseReportViewSet(ApiAccessMixinTest, MyTestCase):

    namespace = 'api:v0:reports'

    def test_serializer_data(self):
        report = CourseReport(
            course=self.course
        )
        report.save()
        response = self.client.get(reverse(self.namespace, kwargs={'course_id': self.course.id}))
        fields_set = {'date', 'response_report'}
        data_set = set(json.loads(response.content)[0])
        self.assertSetEqual(fields_set, data_set)


class TestEchoDataView(MyTestCase):

    namespace = 'api:v0:echo-data'

    def test_echo_405(self):
        get_response = self.client.get(reverse(self.namespace))
        self.assertEqual(get_response.status_code, 405)

    def test_echo_200(self):

        post_response = self.client.post(reverse(self.namespace))
        self.assertEqual(post_response.status_code, 200)

        self.client.logout()

        post_response = self.client.post(reverse(self.namespace))
        self.assertEqual(post_response.status_code, 200)
