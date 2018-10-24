import json
from pymongo.errors import ServerSelectionTimeoutError

from django.core.urlresolvers import reverse
from core.common.mongo import c_onboarding_status

HEALTH_URL = reverse('api:v0:health-check')


def test_health_positive(client, db):
    result = client.get(HEALTH_URL)

    assert result.status_code == 200
    assert 'ok' in json.loads(result.content)


def test_health_non_ok(client, db, mocker):
    """
    Ping and Stats Mongo command return non ok results.
    """
    do_health = mocker.patch('api.v0.views.do_health')
    do_health.return_value = {}, {}

    result = client.get(HEALTH_URL)

    assert result.status_code == 503


def test_health_exception(client, db, mocker):
    """
    Mongo query raises exception.
    """
    do_health = mocker.patch('api.v0.views.do_health')
    do_health.side_effect = ServerSelectionTimeoutError()

    result = client.get(HEALTH_URL)

    assert result.status_code == 503


def test_onboarding_update_data(client, db, user):
    data = {
        'user_id': user.id,
        'step1': 0,
        'step2': 0,
        'step3': 0,
        'step4': 0,
    }
    data_to_update = {'step2': 1}

    c_onboarding_status().insert(data.copy())

    assert client.login(username='admin', password='test_admin') is True
    response = client.put(
        reverse('api:v0:update-onboarding-status'),
        data=json.dumps(data_to_update),
        content_type="application/json"
    )
    assert response.status_code == 200

    data.update(data_to_update)

    mongo_data = c_onboarding_status().find_one(data)

    assert mongo_data is not None

    # need to delete these entries after test is test_post_valid_password_changedone
    c_onboarding_status().remove()

