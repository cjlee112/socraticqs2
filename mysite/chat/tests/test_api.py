"""
Test brella APIs.
"""
import pytest
import unittest
from django.shortcuts import reverse
from django.contrib.auth.models import User
from rest_framework import status

from ct.models import UnitLesson, Lesson
from chat.models import Message


@pytest.mark.django_db
def test_brella_blocked(chat_brella, client):
    """
    Test unauthenticated case for the brella chat API.
    """
    response = client.get(f'/chat/brella/chat?chat_id={chat_brella.id}')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_brella_access(chat_brella, unit_lesson, client):
    """
    Test positive case for the brella chat API.
    """
    client.force_login(chat_brella.user)
    response = client.get(f'/chat/brella/chat?chat_id={chat_brella.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['course']['title'] == chat_brella.enroll_code.courseUnit.course.title
    assert response.data['threads'] == [dict(title=unit_lesson.lesson.title, thread_id=unit_lesson.id)]


@pytest.mark.django_db
def test_brella_threads(chat_brella, lesson_answer_canvas, user_profile, client):
    """
    Test positive case for the brella chat API.
    """
    client.force_login(chat_brella.user)
    response = client.get(f'/chat/brella/threads?chat_id={chat_brella.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['thread_id'] == lesson_answer_canvas.id



@pytest.mark.django_db
def test_messages_blocked(chat_brella, lesson_answer_canvas, user_profile, client):
    """
    Test unauthenticated case for the brella messages API.
    """
    post_data = create_post_data(chat_brella.id, lesson_answer_canvas.id)
    response = client.post('/chat/brella/messages', data=post_data,
                           content_type='application/json', HTTP_ACCEPT='application/json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_messages_json1(chat_brella, brella_messages_json1, user_profile, client):
    """
    Test basic student response for the brella messages API.
    """
    client.force_login(chat_brella.user)
    response = client.post('/chat/brella/messages', data=brella_messages_json1,
                           content_type='application/json', HTTP_ACCEPT='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    m = Message.objects.filter(chat=chat_brella).first()
    assert m.response_to_check.text == brella_messages_json1['message']





def create_post_data(chat_id, thread_id):
    return dict(chat_id=chat_id, thread_id=thread_id)

