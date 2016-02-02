from rest_framework import serializers

from ct.models import Response, StudentError, UnitLesson


class ResponseSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField()
    author_name = serializers.SerializerMethodField()
    lti_identity = serializers.SerializerMethodField()
    unitLesson_id = serializers.IntegerField()
    unit_id = serializers.SerializerMethodField()

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
            'unit_id',
        )

    def get_author_name(self, obj):
        """
        Returning author name.
        """
        name = obj.author.get_full_name()
        if not name:
            name = obj.author.username
        return name

    def get_lti_identity(self, obj):
        """
        Returning LTI user_id.
        """
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            return lti_user.user_id

    def get_unit_id(self, obj):
        """
        Returning Unit id.
        """
        return obj.unitLesson.unit.id


class UnitLessonSerializer(serializers.ModelSerializer):
    """
    UnitLesson serializer for ErrorSerializer.
    """
    lesson_concept_id = serializers.SerializerMethodField()
    lesson_concept_isAbort = serializers.SerializerMethodField()
    lesson_concept_isFail = serializers.SerializerMethodField()
    lesson_text = serializers.SerializerMethodField()

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

    def get_lesson_concept_id(self, obj):
        return obj.lesson.concept.id

    def get_lesson_concept_isAbort(self, obj):
        return obj.lesson.concept.isAbort

    def get_lesson_concept_isFail(self, obj):
        return obj.lesson.concept.isFail

    def get_lesson_text(self, obj):
        return obj.lesson.text


class ErrorSerializer(serializers.ModelSerializer):
    response_id = serializers.IntegerField()
    author_id = serializers.IntegerField()
    errorModel_id = serializers.IntegerField()
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
