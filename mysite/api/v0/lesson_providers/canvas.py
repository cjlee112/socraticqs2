import base64
import secrets

from django.core.files.base import ContentFile

from ct.models import Lesson
from .multichoice import SubKindBaseProvider


class CanvasProvider(SubKindBaseProvider):
    """
    CanvasProvide creates Draw ORCT Lesson.

    It is intended to get a base64 encoded image
    from an API data to transform in into an Image and
    add it to the Lesson.attachment field.
    """
    SUB_KIND = Lesson.CANVAS

    def extra(self):
        """
        Generate an Image attachment based on base64 data.

        API request data must contain `canvas` field with
        base64 encoded image.
        """
        _ext = "jpg"
        _attachment = ContentFile(
            base64.b64decode(self._data["canvas"]),
            name=f"canvas_question_{secrets.token_hex(15)}." + _ext)

        return {
            "attachment": _attachment
        }


class CanvasProviderBuilder:
    """
    CanvasProvider specific builder.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, data, unit, **_ignored):
        """
        Call authorize method, save client and return it.
        """
        self._instance = CanvasProvider(data, unit)

        return self._instance
