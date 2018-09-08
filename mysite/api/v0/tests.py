import json
from pymongo.errors import ServerSelectionTimeoutError

from django.core.urlresolvers import reverse

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
