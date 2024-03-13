"""
Test v0 APIs.
"""
import pytest
from django.shortcuts import reverse
from django.contrib.auth.models import User
from rest_framework import status

from ct.models import UnitLesson, Lesson, Role
from ctms.models import Invite
from accounts.models import Profile, Instructor

import base64
import hashlib
from urllib.parse import urlparse



@pytest.mark.django_db
def test_courselet_threads_get(course_unit, client):
    """
    Test positive case for the threads API.
    """
    response = client.get(reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': course_unit.id}))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_courselet_threads_post(course_unit, client):
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
        reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': course_unit.id}),
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
def test_courselet_threads_delete(course_unit, client):
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
        reverse("api:v0:courselet-threads-list", kwargs={'courselet_pk': course_unit.id}),
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
            'courselet_pk': course_unit.id, "pk": _id}),
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


@pytest.mark.django_db
def test_courselet_threads_update(course_unit, client):
    """
    Test DELETE action for the REST API.
    """
    _data = [
        {
            "title": "Ukraine population.",
            "message": "Ukraine has a population of about 42 million.",
            "kind": "intro"
        }
    ]

    _new_data = {
        "title": "Ukraine population NEW calculation.",
        "message": "Ukraine has a population of about 45 million.",
        "kind": "intro"
    }

    response = client.post(
        reverse("api:v0:courselet-threads-list", kwargs={
            'courselet_pk': course_unit.id}),
        data=_data,
        content_type='application/json',
        HTTP_ACCEPT='application/json'
    )
    result = response.data["result"]
    _id = result[0]["id"]

    response = client.put(
        reverse("api:v0:courselet-threads-detail", kwargs={
            'courselet_pk': course_unit.id, "pk": _id}),
        data=_new_data,
        content_type='application/json',
        HTTP_ACCEPT='application/json'
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["result"]["id"] == _id

    updated_thread = UnitLesson.objects.get(id=_id)
    assert updated_thread.lesson.title == _new_data["title"]
    assert updated_thread.lesson.text == _new_data["message"]


@pytest.mark.django_db
def test_nonadmin_invite(teacher_invite_dict, client):
    'invite API by non-admin user should be forbidden'
    response = client.post(reverse("api:v0:invite"), data=teacher_invite_dict,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_invite_not_instructor(teacher_invite_dict, client, user):
    'invite API by non-instructor user should be forbidden'
    client.force_login(user)
    response = client.post(reverse("api:v0:invite"), data=teacher_invite_dict,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_invite_success(teacher_invite_dict, client, user):
    'invite API by instructor user should succeed'
    client.force_login(user)
    Instructor.objects.create(user=user, institution='institute', what_do_you_teach='something')
    data = teacher_invite_dict.copy()
    data['first_name'] = 'Boris'
    data['last_name'] = 'Karloff'
    response = client.post(reverse("api:v0:invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_invite_teacher(teacher_invite_dict, client, user, unique_instructor, course_unit):
    'invite API by invited teacher should succeed'
    client.force_login(user)
    instructor = Instructor.objects.create(user=unique_instructor, institution='institute', what_do_you_teach='something')
    invite = Invite.create_new(True, course_unit.course, instructor, user.email, 'teacher', None)
    invite.status = 'joined' # user must be an invited teacher to send new teacher Invite
    invite.save()
    course_unit.data = dict(onboarding=dict(teacher='production')) # mark this as onboarding target
    course_unit.save()
    course_unit.course.addedBy = unique_instructor # onboarding course owner must be an Instructor
    course_unit.course.save()
    data = teacher_invite_dict.copy()
    data['first_name'] = 'Boris'
    data['last_name'] = 'Karloff'
    response = client.get(reverse("api:v0:invite"), HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['canInvite']
    response = client.post(reverse("api:v0:invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_invite_teacher_fail(teacher_invite_dict, client, user, unique_instructor, course_unit):
    'invite API from uninvited user should fail'
    client.force_login(user)
    instructor = Instructor.objects.create(user=unique_instructor, institution='institute', what_do_you_teach='something')
    course_unit.data = dict(onboarding=dict(teacher='production')) # mark this as onboarding target
    course_unit.save()
    course_unit.course.addedBy = unique_instructor # onboarding course owner must be an Instructor
    course_unit.course.save()
    data = teacher_invite_dict.copy()
    data['first_name'] = 'Boris'
    data['last_name'] = 'Karloff'
    response = client.get(reverse("api:v0:invite"), HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert not response.data['canInvite']
    response = client.post(reverse("api:v0:invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ech_not_admin(client, user):
    'ECH API by non-admin user should be forbidden'
    client.force_login(user)
    response = client.get(reverse("api:v0:external-content-hash") + '?hashID=bogus&hashID=invalid', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_ech_get(client, user):
    'ECH API by admin user should be allowed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.get(reverse("api:v0:external-content-hash") + '?hashID=bogus&hashID=invalid', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data['missing']) == set(['bogus', 'invalid']) and response.data['found'] == []



@pytest.mark.django_db
def test_ech_post(ech_example1, client, user):
    'ECH API POST by admin user should be allowed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.post(reverse("api:v0:external-content-hash"), data=ech_example1,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['result']['hashID'] == ech_example1['hashID']
    print(f"clientURL: {response.data['result']['clientURL']}")
    assert response.data['result']['clientURL'].endswith(ech_example1['hashID'] + ech_example1['extension'])
    response = client.get(reverse("api:v0:external-content-hash"), data=dict(hashID=ech_example1['hashID']),
                          HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['missing'] == [] and response.data['found'][0]['hashID'] == ech_example1['hashID']


@pytest.mark.django_db
def test_courses_not_admin(client, user, course_json1):
    'course creation API by non-admin user should be forbidden'
    client.force_login(user)
    response = client.post(reverse("api:v0:courses"), data=course_json1,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN



@pytest.mark.django_db
def test_courses_post(client, user, course_json1):
    'course creation API by admin user should succeed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.post(reverse("api:v0:courses"), data=course_json1,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data['courselets']) == 2


@pytest.mark.django_db
def test_courses_badid(client, user, course_json2):
    'course creation API with bad unit_id should fail'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.post(reverse("api:v0:courses"), data=course_json2,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_courses_goodid(client, user, course_json3):
    'course creation API with good unit_id should succeed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.post(reverse("api:v0:courses"), data=course_json3,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data['courselets']) == 2
    assert response.data['courselets'][0]['unit_id'] == course_json3['units'][0]['unit_id']


@pytest.mark.django_db
def test_threads2html_post(course_unit, client, user, threads2html_data1):
    'threads2html upload API by admin user should succeed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    response = client.post(reverse("api:v0:threads2html", kwargs={"pk": course_unit.id}), data=threads2html_data1,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data) == 1
    result = response.data[0]
    assert isinstance(result.get('ul_id', 'missing!'), int)
    assert isinstance(result.get('answer_ul_id', 'missing!'), int)


@pytest.mark.django_db
def test_accinv_not_admin(client, user, pending_invite, dkim_validation_dict):
    'accept-invite API by non-admin user should be forbidden'
    client.force_login(user)
    data = dkim_validation_dict.copy()
    data['code'] = pending_invite.code
    response = client.post(reverse("api:v0:accept-invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_accinv_post(client, user, pending_invite, dkim_validation_dict):
    'accept-invite API by admin user should succeed'
    client.force_login(user)
    user.is_staff = True
    user.save()
    data = dkim_validation_dict.copy()
    data['code'] = pending_invite.code
    assert pending_invite.user.profile.is_provisional()
    response = client.post(reverse("api:v0:accept-invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Invite.objects.filter(code=pending_invite.code, status='joined').exists()
    assert not Profile.objects.get(user=pending_invite.user).is_provisional()
    assert User.objects.get(id=pending_invite.user.id).email == data['email']
    response = client.post(reverse("api:v0:accept-invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST # should block attempt to reuse invite


@pytest.mark.django_db
def test_accinv_badcode(client, user, pending_invite, dkim_validation_dict):
    'accept-invite API with invalid invite code should fail'
    client.force_login(user)
    user.is_staff = True
    user.save()
    data = dkim_validation_dict.copy()
    data['code'] = 'invalid code'
    response = client.post(reverse("api:v0:accept-invite"), data=data,
                           content_type='application/json', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST # should block bad invite


@pytest.mark.django_db
def test_chatstats_not_admin(client, user):
    'chatStats API by non-admin user should be forbidden'
    client.force_login(user)
    response = client.get('/api/v0/chatStats/?startTime=0', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN



@pytest.mark.django_db
def test_chatstats_nonesuch(client, user):
    'chatStats API should reject non-existent namedView'
    client.force_login(user)
    response = client.get('/api/v0/chatStats/?namedView=nonesuch', HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_404_NOT_FOUND




@pytest.mark.django_db
def test_chatstats_basic(client, user, msg_response_brella):
    client.force_login(user)
    user.is_superuser = True
    user.save()
    good = False
    for result in iter_paginated_get(client, '/api/v0/chatStats/', data=dict(startTime=0),
                                     HTTP_ACCEPT='application/json'):
        if result['id'] == msg_response_brella.chat_id:
            assert result['nresp'] == 1
            good = True
    if not good:
        raise AssertionError('missing chat response data')



def iter_paginated_get(clientObj, path, data=None, **kwargs):
    'iterate over all results from Django REST pagination'
    while path:
        response = clientObj.get(path, data, **kwargs)
        assert response.status_code == status.HTTP_200_OK
        dataPage = response.data
        for r in dataPage.get('results', ()):
            yield r
        path = dataPage.get('next', None) # URL for next page
        if path:
            path = urlparse(path).path # always use relative path
            data = None # don't resend params after first page



@pytest.mark.django_db
def test_chatstats2_not_instructor(client, user):
    'chatStats CourseletChats API by non-instructor user should be forbidden'
    client.force_login(user)
    response = client.get('/api/v0/chatStats/?startTime=0&namedView=CourseletChats',
                          HTTP_ACCEPT='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN



@pytest.mark.django_db
def test_chatstats_courselet(client, user, msg_response_brella, chatstats_courselet_json):
    'instructor access to CourseletChats API'
    role = Role.objects.create(role=Role.INSTRUCTOR, user=user,
                               course=msg_response_brella.chat.enroll_code.courseUnit.course)
    client.force_login(user)
    good = False
    for result in iter_paginated_get(client, '/api/v0/chatStats/',
                                     data=chatstats_courselet_json,
                                     HTTP_ACCEPT='application/json'):
        if result['id'] == msg_response_brella.chat_id:
            assert result['nresp'] == 1
            assert result['email'] == 'me@example.com'
            good = True
    if not good:
        raise AssertionError('missing chat response data')



