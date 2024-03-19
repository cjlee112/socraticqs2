"""
Test brella APIs.
"""
import pytest
import unittest
import json
from django.shortcuts import reverse
from django.contrib.auth.models import User
from rest_framework import status

from ct.models import UnitLesson, Lesson, Response
from chat.models import Message
from chat.views import ChatInitialView, annotate_chat_sessions


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





@pytest.mark.django_db
def test_chat_lessons_done(chat_brella, brella_messages_json1, brella_messages_json2, user_profile, client):
    """
    Test ChatInitialView lessons_done annotation.
    """
    client.force_login(chat_brella.user)
    response = client.post('/chat/brella/messages', data=brella_messages_json1,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    data = brella_messages_json2.copy() # student confidence
    data['response_id'] = response.data['response_id']
    response = client.post('/chat/brella/messages', data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert Message.objects.filter(chat=chat_brella).count() == 2
    v = ChatInitialView()
    chat_sessions = v.get_chat_sessions(chat_brella.user, chat_brella.enroll_code,
                                        chat_brella.enroll_code.courseUnit)
    annotate_chat_sessions(chat_sessions)
    assert chat_sessions[0].lessons_done == 1


@pytest.mark.django_db
def test_em_response_status(chat_brella, brella_messages_json3, client):
    client.force_login(chat_brella.user)
    response = client.post('/chat/brella/messages', data=brella_messages_json3,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    r = Response.objects.get(id=brella_messages_json3['response_id'])
    assert r.status == brella_messages_json3['outcome']


@pytest.mark.django_db
def test_response_selfeval(chat_brella, brella_messages_json4, client):
    client.force_login(chat_brella.user)
    response = client.post('/chat/brella/messages', data=brella_messages_json4,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    r = Response.objects.get(id=brella_messages_json4['response_id'])
    assert r.selfeval == brella_messages_json4['outcome']


@pytest.mark.django_db
def test_response_status(chat_brella, brella_messages_json5, client):
    client.force_login(chat_brella.user)
    response = client.post('/chat/brella/messages', data=brella_messages_json5,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    r = Response.objects.get(id=brella_messages_json5['response_id'])
    assert r.status == brella_messages_json5['outcome']


@pytest.mark.django_db
def test_messages_bad_patch(message_brella, client):
    'forbidden to patch unless special case matched (see test_messages_patch)'
    data = dict(message_id=message_brella.id, outcome='no')
    client.force_login(message_brella.owner)
    response = client.patch('/chat/brella/messages', data=data,
                            content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data['message_id'] =  295601
    response = client.patch('/chat/brella/messages', data=data,
                            content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_messages_patch(message_solicit_faq, client):
    'patch answer.solicit_faq to outcome=no should succeed'
    data = json.loads(message_solicit_faq.text)
    assert data['outcome'] == 'yes'
    data = dict(message_id=message_solicit_faq.id, outcome='no')
    response = client.patch('/chat/brella/messages', data=data,
                            content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    client.force_login(message_solicit_faq.owner)
    response = client.patch('/chat/brella/messages', data=data,
                            content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_204_NO_CONTENT
    m = Message.objects.get(id=message_solicit_faq.id)
    data = json.loads(m.text)
    assert data['outcome'] == 'no'



def create_post_data(chat_id, thread_id):
    return dict(chat_id=chat_id, thread_id=thread_id)

