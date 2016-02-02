from rest_framework import viewsets

from ct.serializers import ResponseSerializer
from ct.models import Response


class ResponseViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course report.
    """
    queryset = Response.objects.filter(kind='orct', unitLesson__order__isnull=False)
    serializer_class = ResponseSerializer

    def get_queryset(self):
        queryset = super(ResponseViewSet, self).get_queryset()
        course_id = self.kwargs.get('course_id')
        if course_id:
            queryset = queryset.filter(course__id=course_id)
        return queryset
