from rest_framework import serializers
from django.db.models import Q
from django.core.files.base import ContentFile
from django.utils import timezone

from ct.models import Response, StudentError, UnitLesson, Unit, Lesson, SubKindMixin, ExternalContentHash
from ctms.models import BestPractice1, BestPractice2
from analytics.models import CourseReport
from ct.templatetags.ct_extras import md2html
import datetime
import base64
import hashlib


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

##############################################################################
# brella backend

class ResponseSerializer2(serializers.BaseSerializer):
    'serializer for student response'
    def to_representation(self, r):
        data = dict(response_id=r.id, message=r.text, status=r.status, confidence=r.confidence,
                    atime=r.atime.timetuple(), selfeval=r.selfeval, user_id=r.author.id)
        if r.attachment:
            data['image'] = r.attachment.url
        return data


class StudentErrorSerializer(serializers.BaseSerializer):
    'serializer for student error'
    def to_representation(self, se):
        return dict(student_error_id=se.id, status=se.status, atime=se.atime.timetuple(),
                    response_id=se.__dict__['response_id'], user_id=se.__dict__['author_id'])


class FAQSerializer2(serializers.BaseSerializer):
    'serializer for FAQ student question'
    def to_representation(self, f):
        data = dict(faq_id=f.id, title=f.title, message=f.text, ul_id=f.unitLesson.id,
                    atime=f.atime.timetuple(), user_id=f.author.id)
        if f.kind == f.COMMENT:
            data['parent_id'] = f.parent.id
        if f.unitLesson.parent: # sublesson
            data['thread_id'] = f.unitLesson.parent.id
        else: # top-level lesson
            data['thread_id'] = f.unitLesson.id
        return data

class FAQSerializer3(FAQSerializer2):
    'include InquiryCount data for this FAQ'
    def to_representation(self, f):
        data = FAQSerializer2.to_representation(self, f)
        data['inquiries'] = inquiries = []
        for inquiry in f.inquirycount_set.all():
            inquiries.append(dict(inquiry_id=inquiry.id, status=inquiry.status,
                                  atime=inquiry.atime.timetuple(), user_id=inquiry.addedBy.id))
        return data

class ULSerializer2(serializers.BaseSerializer):
    'base UnitLesson serializer for brella API'
    _faqSerializer = FAQSerializer2
    _faqaSerializer = FAQSerializer2
    def to_representation(self, ul):
        data = dict(kind=ul.lesson.kind, ul_id=ul.id, title=ul.lesson.title, message=md2html(ul.lesson.text),
                    atime=ul.atime.timetuple())
        if ul.lesson.attachment:
            data['image'] = ul.lesson.attachment.url
        if ul.lesson.text2html: # include pre-formatted HTML if provided
            data['text2html'] = ul.lesson.text2html
        faqs = []
        faq_answers = []
        for f in ul.response_set.filter(Q(kind=Response.STUDENT_QUESTION) | Q(kind=Response.COMMENT)):
            if f.kind == f.STUDENT_QUESTION:
                faqs.append(self._faqSerializer(f).data)
            else:
                faq_answers.append(self._faqaSerializer(f).data)
        data['faqs'] = faqs
        data['faq_answers'] = faq_answers
        return data

class ULSerializer3(ULSerializer2):
    'include FAQ InquiryCounts'
    _faqSerializer = FAQSerializer3
    _faqaSerializer = FAQSerializer2

class EMSerializer3(ULSerializer3):
    'include StudentError data for this EM'
    def to_representation(self, ul):
        data = ULSerializer3.to_representation(self, ul)
        data['studenterrors'] = students = []
        for se in ul.studenterror_set.all():
            students.append(dict(student_error_id=se.id, status=se.status, atime=se.atime.timetuple(),
                                 response_id=se.response.id, user_id=se.author.id))
        return data


class ORCTSerializer2(serializers.BaseSerializer):
    'question serializer for brella API'
    _ulSerializer = ULSerializer2
    _emSerializer = ULSerializer2
    def to_representation(self, ul):
        data = dict(kind='orct', title=ul.lesson.title)
        data['question'] = self._ulSerializer(ul).data
        for a in ul.get_answers():
            data['answer'] = self._ulSerializer(a).data
            break
        if ul.lesson.sub_kind == SubKindMixin.CANVAS:
            data['question']['canvas'] = dict(image=ul.lesson.attachment.url)
            if a.lesson.attachment:
                answerURL = a.lesson.attachment.url
            else:
                answerURL = None
            data['answer']['canvas'] = dict(image=ul.lesson.attachment.url, canvasURL=answerURL)
        errors = []
        for em in ul.get_errors():
            errors.append(self._emSerializer(em).data)
        data['errormodels'] = errors
        return data

class ORCTSerializer3(ORCTSerializer2):
    'include Responses, StudentErrors and InquiryCounts in output'
    _ulSerializer = ULSerializer3
    _emSerializer = EMSerializer3
    def to_representation(self, ul):
        data = ORCTSerializer2.to_representation(self, ul)
        data['responses'] = responses = []
        for r in ul.response_set.filter(kind=Response.ORCT_RESPONSE):
            responses.append(ResponseSerializer2(r).data)
        return data


class Text2HtmlULSerializer(serializers.BaseSerializer):
    'question serializer for brella API'
    _ulSerializer = ULSerializer2
    _emSerializer = ULSerializer2
    _optionalFields = ('sub_kind', 'textFormat', 'data',)
    def to_representation(self, ul):
        data = dict(kind=ul.lesson.kind, sub_kind=ul.lesson.sub_kind, title=ul.lesson.title)
        data['question'] = self._ulSerializer(ul).data
        return data
    def to_internal_value(self, data):
        'deserialize input data dict into validated attr dict'
        valid = dict(title=data['title'], text=data['text'], kind=data['kind'], addedBy=data['addedBy'],
                     unit=data['unit'], text2html=data['text2html'], commitTime=timezone.now())
        valid.update({f:data[f] for f in self._optionalFields if f in data})
        echIDs = data.get('echfiles', ())
        if echIDs: # save references to ExternalContentHash
            echfiles = []
            for hashID in echIDs:
                echfiles.append(ExternalContentHash.objects.get(hashID=hashID))
            valid['echfiles'] = echfiles
        if 'answer' in data:
            answer = data['answer']
            answer['commitTime'] = timezone.now()
            if 'title' not in answer:
                answer['title'] = data['title'] + ' Answer'
            valid['answer'] = answer
        return valid # validated data dict
    def create(self, validated_data):
        'save Lesson and UnitLesson'
        unit = validated_data['unit']
        del validated_data['unit']
        answerData = validated_data.get('answer', None)
        if answerData:
            del validated_data['answer']
        lesson = Lesson(**validated_data)
        lesson.save_root()
        ul = UnitLesson.create_from_lesson(lesson, unit, order='APPEND', addAnswer=(answerData is not None),
                                           answerArgs=answerData)
        return ul


def get_ul_serializer(ul, _orctSerializer=ORCTSerializer2, _ulSerializer=ULSerializer2):
    if ul.lesson.kind == Lesson.ASSESSMENT:
        return Text2HtmlULSerializer(ul)
    elif ul.lesson.kind == Lesson.ORCT_QUESTION:
        return _orctSerializer(ul)
    else: # treat as a simple explanation
        return _ulSerializer(ul)

class UnitSerializer2(serializers.BaseSerializer):
    'serializer for an entire courselet'
    def to_representation(self, unit):
        data = []
        for ul in unit.unitlesson_set.filter(order__isnull=False):
            data.append(get_ul_serializer(ul).data)
        return data


class TrivialSerializer(serializers.BaseSerializer):
    'serializer that just echoes input dict'
    def to_representation(self, d):
        for k,v in list(d.items()):
            if isinstance(v, datetime.timedelta):
                d[k] = v.total_seconds()
            elif isinstance(v, datetime.datetime):
                d[k] = v.timestamp()
        return d


class ECHSerializer(serializers.BaseSerializer):
    'serializer for ExternalContentHash'
    def to_representation(self, ech):
        data = dict(hashID=ech.hashID, mimeType=ech.mimeType, clientURL=ech.attachment.url, data=ech.data,
                    atime=ech.atime.timestamp())
        if ech.addedBy:
            data['addedBy'] = ech.addedBy.username
        return data
    def to_internal_value(self, data):
        'deserialize input data dict into validated attr dict'
        imageData = base64.b64decode(data['base64data'])
        hashID = hashlib.sha256(imageData).hexdigest()
        if hashID != data['hashID']:
            raise serializers.ValidationError(f'hashID {data["hashID"]} does not match base64data {hashID}')
        valid = dict(attachment=ContentFile(imageData, name=f'{hashID}{data["extension"]}'))
        for k in ('hashID', 'mimeType', 'data', 'addedBy'):
            valid[k] = data[k]
        valid['data']['extension'] = data['extension']
        return valid # validated data dict
    def create(self, validated_data):
        return ExternalContentHash.objects.create(**validated_data)



