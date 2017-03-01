from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication

from ..serializers import ResponseSerializer, ErrorSerializer
from ..permissions import IsInstructor
from ct.models import Response, StudentError, Course


class ResponseViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course student responses report.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = Response.objects.filter(kind='orct', unitLesson__order__isnull=False)
    serializer_class = ResponseSerializer

    def get_queryset(self):
        self.check_object_permissions(
            self.request, Course.objects.filter(id=self.kwargs.get('course_id')).first()
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
        self.check_object_permissions(
            self.request, Course.objects.filter(id=self.kwargs.get('course_id')).first()
        )
        queryset = super(ErrorViewSet, self).get_queryset()
        return queryset.filter(response__course__id=self.kwargs.get('course_id'))
