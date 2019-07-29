from rest_framework import serializers

from ct.models import Response, StudentError, UnitLesson
from ctms.models import BestPractice1, BestPractice2
from analytics.models import CourseReport


class ResponseSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField()
    author_name = serializers.SerializerMethodField()
    lti_identity = serializers.SerializerMethodField()
    unitLesson_id = serializers.ReadOnlyField()
    courselet_id = serializers.ReadOnlyField(source='unitLesson.unit.id')
    submitted_time = serializers.SerializerMethodField()

    class Meta:
        model = Response
        fields = (
            'id',
            'author_id',
            'author_name',
            'lti_identity',
            'text',
            'confidence',
            'selfeval',
            'status',
            'unitLesson_id',
            'courselet_id',
            'submitted_time',
        )

    def get_author_name(self, obj):
        """
        Returning author name.
        """
        return obj.author.get_full_name() or obj.author.username

    def get_lti_identity(self, obj):
        """
        Returning LTI user_id.
        """
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            return lti_user.user_id

    def get_submitted_time(self, obj):
        """
        Return Response submitted time.
        """
        return obj.atime.strftime("%d-%m-%Y-%H:%M:%S")


class UnitLessonSerializer(serializers.ModelSerializer):
    """
    UnitLesson serializer for ErrorSerializer.
    """
    lesson_concept_id = serializers.ReadOnlyField(source='lesson.concept.id')
    lesson_concept_isAbort = serializers.ReadOnlyField(source='lesson.concept.isAbort')
    lesson_concept_isFail = serializers.ReadOnlyField(source='lesson.concept.isFail')
    lesson_text = serializers.ReadOnlyField(source='lesson.text')

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'lesson_concept_id',
            'lesson_concept_isAbort',
            'lesson_concept_isFail',
            'lesson_text',
            'treeID',
        )


class ErrorSerializer(serializers.ModelSerializer):
    response_id = serializers.ReadOnlyField()
    author_id = serializers.ReadOnlyField()
    errorModel_id = serializers.ReadOnlyField()
    em_data = serializers.SerializerMethodField()

    class Meta:
        model = StudentError
        fields = (
            'id',
            'response_id',
            'status',
            'atime',
            'author_id',
            'errorModel_id',
            'em_data',
        )

    def get_em_data(self, obj):
        return UnitLessonSerializer().to_representation(obj.errorModel)


class CourseReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReport
        fields = ('date', 'response_report')


class BestPractice1Serializer(serializers.ModelSerializer):
    class Meta:
        model = BestPractice1
        fields = ('student_count', 'misconceptions_count', 'question_count', 'mean_percent')


class BestPractice1PdfSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPractice1
        fields = ('pdf',)


class BestPractice2Serializer(serializers.ModelSerializer):
    class Meta:
        model = BestPractice2
        fields = ('percent_engaged',)
