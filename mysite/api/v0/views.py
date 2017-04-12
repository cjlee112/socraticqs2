from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response as RestResponse

from ..serializers import ResponseSerializer, ErrorSerializer, CourseReportSerializer
from ..permissions import IsInstructor
from ct.models import Response, StudentError, Course
from analytics.tasks import report
from analytics.models import CourseReport


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
        if not course.addedBy == request.user:
            return RestResponse('action is not allowed', status=403)
        report.delay(course_id)
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
