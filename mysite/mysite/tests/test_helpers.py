import pytest
from django.core.files.base import ContentFile
import base64

from mysite.helpers import base64_to_file


BASE64_GIF_IMAGE = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'


@pytest.mark.parametrize('base64,expected', [
    (
        'data:image/gif;base64,{}'.format(BASE64_GIF_IMAGE),
        ContentFile(base64.b64decode(BASE64_GIF_IMAGE), name='image.gif')
    ),
    ('bad data', None),
])
def test_base64_to_file(base64, expected):
    assert isinstance(base64_to_file(base64), type(expected))
