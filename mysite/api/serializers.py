from rest_framework import serializers

from ct.models import Response, StudentError, UnitLesson, Unit, Lesson
from ctms.models import BestPractice1, BestPractice2
from analytics.models import CourseReport
from ct.templatetags.ct_extras import md2html


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


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = (
            'title',
            'exam_name',
            'follow_up_assessment_date',
            'follow_up_assessment_grade',
            'question_parts',
            'average_score',
            'courselet_days',
            'courselet_deadline',
            'graded_assessment_value',
            'graded_assessment_datetime',
            'error_resolution_days',
            'courselet_completion_credit',
            'late_completion_penalty',
            'is_show_will_learn',
        )


class ThreadSerializer(serializers.ModelSerializer):
    """
    Serialize Thread aka UnitLesson object.
    """
    kind = serializers.ReadOnlyField(source="lesson.kind")
    title = serializers.ReadOnlyField(source="lesson.title")
    author = serializers.ReadOnlyField(source="lesson.addedBy.username")

    class Meta:
        model = UnitLesson
        fields = ("id", "kind", "title", "author")



class UnitSerializer2(serializers.BaseSerializer):
    def to_representation(self, unit):
        data = []
        for ul in unit.unitlesson_set.filter(order__isnull=False):
            if ul.lesson.kind == Lesson.ORCT_QUESTION:
                d = dict(kind='orct', title=ul.lesson.title)
                d['question'] = dict(ulID=ul.id, message=md2html(ul.lesson.text))
                for a in ul.get_answers():
                    d['answer'] = dict(ulID=a.id, message=md2html(a.lesson.text))
                    faqs = []
                    for f in a.response_set.filter(kind=Response.STUDENT_QUESTION):
                        faqs.append(dict(title=f.title, question=f.text, answerTitle='Instructor Answer', answer='You bet.'))
                    d['answer']['faqs'] = faqs
                    break
                errors = []
                for em in ul.get_errors():
                    errors.append(dict(ulID=em.id, title=em.lesson.title, message=md2html(em.lesson.text)))
                d['errormodels'] = errors
                data.append(d)
            elif ul.lesson.kind == Lesson.BASE_EXPLANATION:
                data.append(dict(kind='intro', ulID=ul.id, title=ul.lesson.title, message=md2html(ul.lesson.text)))
        return data



