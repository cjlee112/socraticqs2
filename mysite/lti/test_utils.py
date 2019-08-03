import pytest

from lti.utils import key_secret_generator


@pytest.mark.unittest
def test_key_secret_generator(mock):
    settings_mock = mock.patch('lti.utils.settings')
    settings_mock.SECRET_KEY = 'testSecret_/Key%'

    value1 = key_secret_generator()
    value2 = key_secret_generator()

    assert not value1 == value2
