"""
Test v0 APIs.
"""
import pytest
from django.shortcuts import reverse
from django.contrib.auth.models import User
from rest_framework import status


@pytest.mark.django_db
def test_courselet_threads_get(unit, client):
    """
    Test positive case for the threads API.
    """
    response = client.get(reverse("api:v0:courselet-threads-api", kwargs={'pk': unit.id}))

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
        reverse("api:v0:courselet-threads-api", kwargs={'pk': unit.id}),
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
