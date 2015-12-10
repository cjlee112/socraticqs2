from rest_framework import serializers

from ct.models import Response


class ResponseSerializer(serializers.HyperlinkedModelSerializer):
    get_author_id = serializers.SerializerMethodField('author_id')
    get_lti_identity = serializers.SerializerMethodField('lti_identity')
    get_unitLesson_id = serializers.SerializerMethodField('unitLesson_id')
    get_unit_id = serializers.SerializerMethodField('unit_id')

    class Meta:
        model = Response
        fields = (
            'id',
            'get_author_id',
            'get_lti_identity',
            'text',
            'confidence',
            'selfeval',
            'status',
            'get_unitLesson_id',
            'get_unit_id'
        )

    def author_id(self, obj):
        """
        Returning author id.
        """
        return obj.author.id

    def lti_identity(self, obj):
        """
        Returning LTI user_id.
        """
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            return lti_user.user_id

    def unitLesson_id(self, obj):
        """
        Returning UnitLesson id.
        """
        return obj.unitLesson.id

    def unit_id(self, obj):
        """
        Returning Unit id.
        """
        return obj.unitLesson.unit.id
