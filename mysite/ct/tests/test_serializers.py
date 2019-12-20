import pytest

from ct.models import Response, UnitLesson
from ct.serializers import (
    BaseQSSerializer,
    QuestionFaqUpdatesSerializer,
    AnswerFaqUpdatesSerializer,
    AnswerFaqCommentsUpdatesSerializer,
    QuestionFaqCommentsUpdatesSerializer,
    EmUpdatesSerializer,
    EmResolutionsSerializer
)


@pytest.mark.django_db
def test_base_qs_serializer(response):
    qs = Response.objects.all()
    default_serializer_whith_fields = BaseQSSerializer(fields=('lesson', 'kind'))
    result1 = default_serializer_whith_fields.serialize(qs)
    expected_result1 = '[{"model": "ct.response", "pk": 1, "fields": {"lesson": 1, "kind": "orct"}}]'
    assert result1 == expected_result1
    xml_serializer_whith_fields = BaseQSSerializer(format='xml', fields=('lesson', 'kind'))
    result2 = xml_serializer_whith_fields.serialize(qs)
    expected_result2 = '<?xml version="1.0" encoding="utf-8"?>\n<django-objects version="1.0"><object model="ct.response" pk="1"><field name="lesson" rel="ManyToOneRel" to="ct.lesson">1</field><field name="kind" type="CharField">orct</field></object></django-objects>'
    assert result2 == expected_result2


@pytest.mark.django_db
def test_question_faq_updates_serializer(response):
    qs = Response.objects.all()
    qfu_serializer = QuestionFaqUpdatesSerializer()
    assert qfu_serializer.fields == ('title', 'text')
    assert qfu_serializer.format == 'json'
    result = qfu_serializer.serialize(qs)
    expected_result = '[{"model": "ct.response", "pk": 1, "fields": {"title": null, "text": "test response"}}]'
    assert result == expected_result


@pytest.mark.django_db
def test_answer_faq_updates_serializer(response):
    qs = Response.objects.all()
    afu_serializer = AnswerFaqUpdatesSerializer()
    assert afu_serializer.fields == ('title', 'text',)
    assert afu_serializer.format == 'json'
    result = afu_serializer.serialize(qs)
    expected_result = '[{"model": "ct.response", "pk": 1, "fields": {"title": null, "text": "test response"}}]'
    assert result == expected_result


@pytest.mark.django_db
def test_question_faq_comments_updates_serializer(response):
    qs = Response.objects.all()
    qfcu_serializer = AnswerFaqCommentsUpdatesSerializer()
    assert qfcu_serializer.fields == ('title', 'text',)
    assert qfcu_serializer.format == 'json'
    result = qfcu_serializer.serialize(qs)
    expected_result = '[{"model": "ct.response", "pk": 1, "fields": {"title": null, "text": "test response"}}]'
    assert result == expected_result


@pytest.mark.django_db
def test_answer_faq_comments_updates_serializer(response):
    qs = Response.objects.all()
    afcu_serializer = QuestionFaqCommentsUpdatesSerializer()
    assert afcu_serializer.fields == ('title', 'text',)
    assert afcu_serializer.format == 'json'
    result = afcu_serializer.serialize(qs)
    expected_result = '[{"model": "ct.response", "pk": 1, "fields": {"title": null, "text": "test response"}}]'
    assert result == expected_result


@pytest.mark.django_db
def test_em_updates_serializer(response):
    qs = UnitLesson.objects.all()
    emu_serializer = EmUpdatesSerializer()
    assert emu_serializer.fields == ('lesson',)
    assert emu_serializer.format == 'json'
    result = emu_serializer.serialize(qs)
    expected_result = '[{"model": "ct.unitlesson", "pk": 1, "fields": {"lesson": [1, "ugh", "brr"]}}]'
    assert result == expected_result

# FIXME: rework after apdating serializer:
@pytest.mark.django_db
def test_em_resolutions_serializer(response):
    qs = UnitLesson.objects.all()
    emr_serializer = EmResolutionsSerializer()
    assert emr_serializer.fields == ('lesson',)
    assert emr_serializer.format == 'json'
    result = emr_serializer.serialize(qs)
    expected_result = '[{"model": "ct.unitlesson", "pk": 1, "fields": {"lesson": [1, "ugh", "brr"]}}]'
    assert result == expected_result
