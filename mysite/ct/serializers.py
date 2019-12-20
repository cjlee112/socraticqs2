from django.core import serializers


class BaseQSSerializer():
    """
    Base serializer class.

    Arguments:
        format (str) - format to serialise in;
        fields (tuple(str)) - fields from queryset to include.
    Returns:
        serialised object.
    """
    def __init__(self, format='json', fields=None):
        self.format = format
        self.fields = fields

    def serialize(self, queryset):
        return serializers.serialize(self.format, queryset, fields=self.fields)


class QuestionFaqUpdatesSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.question_faq_updates.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('title', 'text',)


class AnswerFaqUpdatesSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.answer_faq_updates.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('title', 'text',)


class EmUpdatesSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.em_updates.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('lesson',)

    def serialize(self, queryset):
        """
        Returns natural_key instead of pk for ForeinKey field.
        """
        return serializers.serialize(self.format, queryset, fields=self.fields, use_natural_foreign_keys=True)


class EmResolutionsSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.em_resolutions.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('lesson',)

    def serialize(self, queryset):
        """
        Returns natural_key instead of pk for ForeinKey field.
        """
        # FIXME: rework to serialize a list of QuerySets:
        return serializers.serialize(self.format, queryset, fields=self.fields, use_natural_foreign_keys=True)


class QuestionFaqCommentsUpdatesSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.question_faq_comments_updates.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('title', 'text',)


class AnswerFaqCommentsUpdatesSerializer(BaseQSSerializer):
    """
    Serializer for ct.models.UnitLesson.answer_faq_comments_updates.
    """
    def __init__(self):
        super().__init__()
        self.fields = ('title', 'text',)
