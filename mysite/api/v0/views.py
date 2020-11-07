import time
import logging

from rest_framework import viewsets, status, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import Q

from analytics.models import CourseReport
from analytics.tasks import report
from ct.models import CourseUnit, Response, StudentError, Course, Role, Unit, UnitLesson, Lesson
from ctms.models import BestPractice, BestPracticeTemplate
from core.common.mongo import do_health, c_onboarding_status
from core.common import onboarding
from core.common.utils import get_onboarding_steps, get_onboarding_status_with_settings, create_intercom_event
from ..permissions import IsInstructor
from ..serializers import (
    ResponseSerializer,
    ErrorSerializer,
    CourseReportSerializer,
    UnitSerializer,
    ThreadSerializer,
)
from .utils import get_result_course_calculation, get_result_courselet_calculation
from .creators import ThreadBuilder


logger = logging.getLogger(__name__)


class ResponseViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course student responses report.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = Response.objects.filter(kind='orct', unitLesson__order__isnull=False)
    serializer_class = ResponseSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(ResponseViewSet, self).get_queryset()
        return queryset.filter(course__id=self.kwargs.get('course_id'))


class ErrorViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course student errors report.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = StudentError.objects.all()
    serializer_class = ErrorSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(ErrorViewSet, self).get_queryset()
        return queryset.filter(response__course__id=self.kwargs.get('course_id'))


class GenReportView(APIView):
    """
    Start `report` Celery task for `course_id`.
    """
    authentication_classes = (SessionAuthentication,)

    def get(self, request, format=None):
        course_id = request.GET.get('course_id')
        if not course_id:
            return RestResponse('course_id is not provided', status=400)
        course = get_object_or_404(Course, id=course_id)
        course_instructors = course.role_set.filter(role=Role.INSTRUCTOR).values_list('user_id', flat=True)
        if (
                request.user.id not in course_instructors and
                not course.addedBy == request.user
        ):
            return RestResponse('action is not allowed', status=403)
        report.delay(course_id, request.user.id)
        return RestResponse(status=200)


class CourseReportViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns CourseReports for current Course.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = CourseReport.objects.all()
    serializer_class = CourseReportSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(CourseReportViewSet, self).get_queryset()
        return queryset.filter(course=course)


class EchoDataView(APIView):
    """
    Echoes request post data
    """

    def post(self, request, *args, **kwargs):
        return RestResponse(
            request.data,
            status=status.HTTP_200_OK,
        )


class HealthCheck(APIView):
    """
    Sevice health check.
    """

    def get(self, request, *args, **kwargs):
        # TODO add django-health-check
        response  = None
        try:
            ping, stats = do_health()
        # broad exception to handle all possible error during interaction with MongoDB
        except:
            response = RestResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            if not ('ok' in ping and 'ok' in stats):
                # TODO implement analyzing and return more descriptive response
                response = RestResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                response = RestResponse(ping, status=status.HTTP_200_OK)

        return response


class OnboardingStatus(APIView):

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        steps_to_update = request.data.copy()
        user_id = steps_to_update.pop('user_id', None) or request.user.id
        to_update = {
            k: bool(v) for k, v in list(steps_to_update.items()) if k in get_onboarding_steps()
        }
        if to_update and request.user.id:
            projection = {k: 1 for k, v in list(to_update.items())}
            projection['_id'] = 0
            passed_steps = c_onboarding_status().find_one({onboarding.USER_ID: user_id}, projection) or {}
            for step in to_update:
                if to_update[step] and not passed_steps.get(step):
                    create_intercom_event(
                        event_name='step-completed',
                        created_at=int(time.mktime(time.localtime())),
                        email=request.user.email,
                        metadata={'step': step}
                    )
            c_onboarding_status().update_one({onboarding.USER_ID: user_id}, {'$set': to_update}, upsert=True)
            return RestResponse({'status': 'Ok'}, status=status.HTTP_200_OK)
        return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        data = get_onboarding_status_with_settings(request.user.id)
        if data:
            return RestResponse({'status': 'Ok', 'data': data}, status=status.HTTP_200_OK)


class OnboardingBpAnalysis(APIView):

    authentication_classes = (SessionAuthentication,)

    def post(self, request, *args, **kwargs):
        data = request.data.dict()
        bp_template = BestPracticeTemplate.objects.filter(id=data.pop('best_practice_template_id')).first()
        best_practice = BestPractice.objects.filter(id=data.pop('best_practice_id')).first()
        if bp_template and best_practice:
            data.pop('csrfmiddlewaretoken', None)
            if bp_template.scope == bp_template.COURSELET:
                course_best_practice = best_practice.course.bestpractice_set.filter(
                    template__scope='course', template__slug='practice-exam', courselet=best_practice.courselet
                ).first()
                if course_best_practice and course_best_practice.data:
                    data.update({'base': course_best_practice.data.get('result_data', {}).get('w_courselets')})
                result_data = get_result_courselet_calculation(data, bp_template.calculation)
            else:
                result_data = get_result_course_calculation(data, bp_template.calculation)
            best_practice.data.update({'input_data': data, 'result_data': result_data})
            best_practice.save()
            best_practice.course.apply_from(data, commit=True)
            best_practice.courselet.unit.apply_from(data, commit=True) if best_practice.courselet else None
            return RestResponse({'status': 'Ok', 'result_data': result_data}, status=status.HTTP_200_OK)
        return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class BestPracticeCreate(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        bp_template = BestPracticeTemplate.objects.filter(id=int(request.POST.get('template_id'))).first()
        data = {}
        if bp_template:
            data["input_data"] = {key: value.get("default") for key, value in bp_template.calculation.items()}
            if bp_template.scope == bp_template.COURSELET:
                data["result_data"] = get_result_courselet_calculation(data["input_data"], bp_template.calculation)
            else:
                data["result_data"] = get_result_course_calculation(data["input_data"], bp_template.calculation)

        try:
            courselet_id = int(request.POST.get('courselet_id')) if request.POST.get('courselet_id') else None
            new_best_practice = BestPractice.objects.create(
                template_id=int(request.POST.get('template_id')),
                course_id=int(request.POST.get('course_id')),
                courselet_id=courselet_id,
                data=data
            )
            if data:
                new_best_practice.data.update(data)
                new_best_practice.save()
                new_best_practice.course.apply_from(data, commit=True)
                new_best_practice.courselet.unit.apply_from(data, commit=True) if new_best_practice.courselet else None
            return RestResponse({'status': 'Ok', 'data': {'new_best_practice': new_best_practice.id}}, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(e)
            return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class BestPracticeUpload(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if request.POST.get('best_practice_id'):
            best_practice = BestPractice.objects.filter(id=int(request.POST.get('best_practice_id'))).first()
            best_practice.upload_file = request.data.get('upload_file')
            best_practice.save()
            create_intercom_event(
                event_name='exam-upload',
                created_at=int(time.mktime(time.localtime())),
                email=request.user.email,
                metadata={'document-link': best_practice.upload_file.url}
            )
            return RestResponse({'best_practice_id': best_practice.id}, status=status.HTTP_200_OK)
        else:
            try:
                if request.POST.get('template_id'):
                    template_id = int(request.POST.get('template_id'))
                else:
                    template_id = BestPracticeTemplate.objects.filter(slug='upload-practice-exam').first().id
                new_best_practice = BestPractice.objects.create(
                    template_id=template_id,
                    courselet_id=int(request.POST.get('courselet_id')),
                    upload_file=request.data.get('upload_file'),
                    active=True
                )
                create_intercom_event(
                    event_name='exam-upload',
                    created_at=int(time.mktime(time.localtime())),
                    email=request.user.email,
                    metadata={'document-link': new_best_practice.upload_file.url}
                )
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    mark_safe(f"<b>Your document has been uploaded.</b> We’ll send an email to \
                        {self.request.user.email} once it has been converted, usually in a day or two."))
                return RestResponse({'best_practice_id': new_best_practice.id}, status=status.HTTP_200_OK)
            except ValueError as e:
                logger.error(e)
                return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class CourseletViewSet(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class CourseletThreadsViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all Courselet's threads.
    """
    authentication_classes = (SessionAuthentication,)
    queryset = UnitLesson.objects.all()
    serializer_class = ThreadSerializer

    def get_unit(self, course_unit_pk):
        """
        Get Unit instanfe from a CoureUnit/Courselet object.
        """
        course_unit = get_object_or_404(CourseUnit, id=course_unit_pk)

        return course_unit.unit

    def get_queryset(self):
        """
        Specifying UniLessons aka Threads for the Courselet aka Unit.
        """
        queryset = super().get_queryset()
        unit = self.get_unit(self.kwargs.get("courselet_pk"))

        return queryset.filter(
            Q(lesson__kind=Lesson.ORCT_QUESTION) | Q(lesson__kind=Lesson.BASE_EXPLANATION),
            unit=unit,
            order__isnull=False)

    def create(self, request, courselet_pk, *args, **kwargs):
        """
        Creates list of Threads for the given Courselet.
        """
        unit = self.get_unit(courselet_pk)
        threads = []

        for thread_data in request.data:
            builder = ThreadBuilder(unit)
            threads.append(builder.build(thread_data))

        serializer = self.serializer_class(threads, many=True)

        return RestResponse(
            {
                "status": "created",
                "result": serializer.data
            },
            status=status.HTTP_201_CREATED)

    def update(self, request, courselet_pk, *args, **kwargs):
        """
        Completelly update the Thread with a new data.
        """
        unit = self.get_unit(courselet_pk)
        thread = self.get_object()

        builder = ThreadBuilder(unit)
        undated_thread = builder.update(thread, request.data)

        serializer = self.serializer_class(undated_thread)

        return RestResponse(
            {
                "status": "updated",
                "result": serializer.data
            },
            status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        """
        We need to ensure Lesson instance is deleted.

        Also we have to recalculate an order for a Unit.
        """
        # save Unit to perform reordering
        _unit = instance.unit

        instance.lesson.delete()
        super().perform_destroy(instance)

        _unit.reorder_exercise()
