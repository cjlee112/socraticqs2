import base64
import secrets
import hashlib

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
        _ext = self.get_image_format('canvas')
        _attachment = ContentFile(
            base64.b64decode(self._data["canvas"]),
            name=f"canvas_question_{secrets.token_hex(15)}." + _ext)

        return {
            "attachment": _attachment
        }
    def extra_answer(self):
        if 'answerImg' in self._data:
            _ext = self.get_image_format('answerImg')
            imageData = base64.b64decode(self._data["answerImg"])
            name = f"canvas_answer_{secrets.token_hex(15)}.{_ext}"
            _attachment = ContentFile(imageData, name=name)
            self._response['answerImg'] = dict(sha256=hashlib.sha256(imageData).hexdigest(),
                                               fmt=self._data.get('answerImgfmt', None), name=name)
            return {
                "attachment": _attachment
            }
        else:
            return {}
    def get_image_format(self, kwarg):
        try:
            return self._data[kwarg + 'fmt']
        except KeyError:
            return 'jpg'


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
