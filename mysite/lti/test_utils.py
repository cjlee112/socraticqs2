import pytest
from django.contrib.auth.models import User
from uuid import uuid4
from django.db import IntegrityError, transaction
from lti.utils import key_secret_generator, create_courselets_user, hash_lti_user_data


@pytest.mark.unittest
def test_key_secret_generator(mock):
    settings_mock = mock.patch('lti.utils.settings')
    settings_mock.SECRET_KEY = 'testSecret_/Key%'

    value1 = key_secret_generator()
    value2 = key_secret_generator()

    assert not value1 == value2


@pytest.mark.unittest
@pytest.mark.django_db
def test_create_courselets_user():
    user1 = create_courselets_user()
    user2 = create_courselets_user()

    assert not user1 == user2


@pytest.mark.unittest
def test_integrity_error(mocker):
    create = mocker.patch('lti.utils.User.objects.create_user')
    atomic = mocker.patch('lti.utils.transaction.atomic')

    abs_user = mocker.Mock()
    abs_user2 = mocker.Mock()
    create.side_effect = [IntegrityError, abs_user, abs_user2]

    assert create_courselets_user() == abs_user
    assert create.call_count == 2
    create.reset_mock()
    create.side_effect = [IntegrityError, abs_user, abs_user2]

    assert not create_courselets_user() == abs_user2


@pytest.mark.unittest
@pytest.mark.django_db
@pytest.mark.parametrize("user_id, tool_consumer_instance_guid, lis_person_sourcedid", [
    ('1', 'tool_consumer_instance_guid', 'lis_person_sourcedid'),
    ('2', 'tool_consumer_instance_guid', 'lis_person_sourcedid'), #next time make blank id
    ('3', '', 'lis_person_sourcedid'),
    ('4', 'tool_consumer_instance_guid', ''),
    ('5', '', ''),
])
def test_hash_lti_user_data(user_id, tool_consumer_instance_guid, lis_person_sourcedid):
    new_user = hash_lti_user_data(user_id, tool_consumer_instance_guid, lis_person_sourcedid)
    assert len(new_user) == 30
    assert type(new_user) == str

