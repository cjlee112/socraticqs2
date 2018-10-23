from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from analytics.models import CourseReport
from analytics.tasks import report
from ct.models import Response, StudentError, Course, Role
from core.common.mongo import do_health, c_onboarding_status
from core.common.utils import get_onboarding_steps
from ..permissions import IsInstructor
from ..serializers import ResponseSerializer, ErrorSerializer, CourseReportSerializer


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


class UpdateOnboardingStatus(APIView):

    authentication_classes = (SessionAuthentication, )

    def post(self, request, *args, **kwargs):
        steps_to_update = request.data
        to_update = {
            k: v for k, v in steps_to_update.items() if k in get_onboarding_steps()
        }
        if to_update and request.user.id:
            c_onboarding_status().update_one({'user_id': request.user.id}, {'$set': to_update})
            return RestResponse({'updated': 'Ok'}, status=status.HTTP_200_OK)
        return RestResponse({'updated': 'failed'}, status=status.HTTP_400_BAD_REQUEST)
