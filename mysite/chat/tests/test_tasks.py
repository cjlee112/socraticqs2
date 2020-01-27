import pytest

from chat.tasks import notify_for_updates


@pytest.mark.unittest
@pytest.mark.django_db
def test_notify_for_updates(mocker):
    mock_send_emails = mocker.patch('chat.tasks.send_emails')
    assert notify_for_updates() is None
    assert mock_send_emails.call_count == 0


# TODO: check that no message will be send to a DONE threads