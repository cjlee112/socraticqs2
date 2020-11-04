"""
Test v0 APIs.
"""
import pytest
from django.shortcuts import reverse
from django.contrib.auth.models import User
from rest_framework import status

from ct.models import UnitLesson, Lesson


@pytest.mark.django_db
def test_courselet_threads_get(unit, client):
    """
    Test positive case for the threads API.
    """
    response = client.get(reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': unit.id}))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_courselet_threads_post(unit, client):
    """
    Test positive case for the threads API.
    """
    _data = [
        {
            "title": "Ukraine population.",
            "message": "Ukraine has a population of about 42 million.",
            "kind": "intro",
            "author": "Ilona"
        },
        {
            "title": "ORCT Ukraine population.",
            "question": "What population of Ukraine?",
            "answer": "Ukraine has a population of about 42 million.",
            "kind": "question",
            "author": "Ilona"
        }
    ]
    author = User.objects.create(username="Ilona")

    response = client.post(
        reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': unit.id}),
        data=_data,
        content_type='application/json',
        HTTP_ACCEPT='application/json'
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "created"
    assert len(response.data["result"]) == 2

    assert response.data["result"][0]["id"]
    assert response.data["result"][0]["kind"] == "base"
    assert response.data["result"][0]["title"] == _data[0]["title"]
    assert response.data["result"][0]["author"] == author.username

    assert response.data["result"][1]["id"]
    assert response.data["result"][1]["kind"] == "orct"
    assert response.data["result"][1]["title"] == _data[1]["title"]
    assert response.data["result"][1]["author"] == author.username


@pytest.mark.django_db
def test_courselet_forbidden_get(unit, client):
    """
    Test forbidden case for the Courselet's GET API request.
    """
    response = client.get(reverse("api:v0:courselet-api", kwargs={'pk': unit.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_courselet_get(unit, client):
    """
    Test positive case for the Courselet API.
    """
    client.force_login(unit.addedBy)
    response = client.get(reverse("api:v0:courselet-api", kwargs={'pk': unit.id}))

    assert response.status_code == status.HTTP_200_OK

    # check all values from API reponse to be identical to
    # the unit fields from DB
    for key, value in response.data.items():
        assert value == getattr(unit, key)


@pytest.mark.django_db
def test_courselet_threads_delete(unit, client):
    """
    Test DELETE action for the REST API.
    """
    _data = [
        {
            "title": "Ukraine population.",
            "message": "Ukraine has a population of about 42 million.",
            "kind": "intro"
        },
        {
            "title": "ORCT Ukraine population.",
            "question": "What population of Ukraine?",
            "answer": "Ukraine has a population of about 42 million.",
            "kind": "question"
        }
    ]

    response = client.post(
        reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': unit.id}),
        data=_data,
        content_type='application/json',
        HTTP_ACCEPT='application/json'
    )
    result = response.data["result"]
    _id = result[0]["id"]

    unit_lesson = UnitLesson.objects.get(id=_id)
    lesson = unit_lesson.lesson

    orct_id = result[1]["id"]
    orct_unit_lesson = UnitLesson.objects.get(id=orct_id)
    orct_lesson = orct_unit_lesson.lesson

    response = client.delete(
        reverse("api:v0:courselet-threads-detail", kwargs={
            'courselet_pk': unit.id, "pk": _id}),
        content_type='application/json',
        HTTP_ACCEPT='application/json'
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(UnitLesson.DoesNotExist):
        UnitLesson.objects.get(id=_id)

    with pytest.raises(Lesson.DoesNotExist):
        Lesson.objects.get(id=lesson.id)

    # Check for the orct thread to stay alive
    Lesson.objects.get(id=orct_lesson.id)

    saved_orct_unit_lesson = UnitLesson.objects.get(id=orct_id)
    assert saved_orct_unit_lesson.order == 0
