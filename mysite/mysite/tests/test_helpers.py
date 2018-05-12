import pytest
from django.core.files.base import ContentFile
import base64

from conftest import base64_gif_image
from mysite.helpers import base64_to_file


@pytest.mark.parametrize('base64,expected', [
    (
            'data:image/gif;base64,{}'.format(base64_gif_image()),
            ContentFile(base64.b64decode(base64_gif_image()), name='image.gif')
    ),
    ('bad data', None),
])
def test_base64_to_file(base64, expected):
    assert isinstance(base64_to_file(base64), type(expected))
