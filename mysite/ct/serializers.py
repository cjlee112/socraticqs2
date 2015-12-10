from rest_framework import serializers

from ct.models import Response


class ResponseSerializer(serializers.HyperlinkedModelSerializer):
    author_id = serializers.SerializerMethodField()
    lti_identity = serializers.SerializerMethodField()
    unitLesson_id = serializers.SerializerMethodField()
    unit_id = serializers.SerializerMethodField()

    class Meta:
        model = Response
        fields = (
            'id',
            'author_id',
            'lti_identity',
            'text',
            'confidence',
            'selfeval',
            'status',
            'unitLesson_id',
            'unit_id',
        )

    def get_author_id(self, obj):
        """
        Returning author id.
        """
        return obj.author.id

    def get_lti_identity(self, obj):
        """
        Returning LTI user_id.
        """
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            return lti_user.user_id

    def get_unitLesson_id(self, obj):
        """
        Returning UnitLesson id.
        """
        return obj.unitLesson.id

    def get_unit_id(self, obj):
        """
        Returning Unit id.
        """
        return obj.unitLesson.unit.id
