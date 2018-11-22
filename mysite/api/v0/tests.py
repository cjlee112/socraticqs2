import json
from pymongo.errors import ServerSelectionTimeoutError

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from core.common.mongo import c_onboarding_status, _conn, DB_DATA
from core.common import onboarding

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
    # Hack: remove collection before test
    c_onboarding_status().remove()
    data = {
        onboarding.USER_ID: user.id,
        onboarding.STEP_1: False,
        onboarding.STEP_2: False,
        onboarding.STEP_3: False,
        onboarding.STEP_4: False,
    }
    data_to_update = {onboarding.STEP_2: True}

    c_onboarding_status().insert(data.copy())
    ensure_saved = c_onboarding_status().find_one({onboarding.USER_ID: user.id}, {'_id': False})

    assert ensure_saved == data

    assert client.login(username='admin', password='test_admin') is True
    response = client.put(
        reverse('api:v0:onboarding-status'),
        data=json.dumps(data_to_update),
        content_type="application/json"
    )
    assert response.status_code == 200
    data.update(data_to_update)
    mongo_data = c_onboarding_status().find_one({onboarding.USER_ID: user.id}, {'_id': False})

    assert mongo_data == data

    # need to delete db after test test_post_valid_password_change done
    _conn.connector.drop_database(DB_DATA)

