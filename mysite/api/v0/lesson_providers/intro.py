import base64
import secrets

from django.core.files.base import ContentFile

from django.contrib.auth.models import User

from ct.models import Lesson


class IntroProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def _convert_data(self):
        """
        By default return data["message"].
        """
        return self._data.get("message", "")

    def extra(self):
        """
        Generate an Image attachment based on base64 data.

        API request data must contain `canvas` field with
        base64 encoded image.
        """
        if not self._data.get("image"):
            return {}

        _ext = "jpg"
        _attachment = ContentFile(
            base64.b64decode(self._data["image"]),
            name=f"orct_image_{secrets.token_hex(15)}." + _ext)

        return {
            "attachment": _attachment
        }

    def get_intro(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._convert_data(),
            "kind": Lesson.BASE_EXPLANATION,
            "treeID": 1,
            "addedBy": author or self._unit.addedBy,
        }
        _converted.update(self.extra())

        intro = Lesson(**_converted)
        intro.save()

        return intro


class IntroProviderBuilder:
    """
    IntroProvider specific builder.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, data, unit, **_ignored):
        """
        Call authorize method, save client and return it.
        """
        self._instance = IntroProvider(data, unit)

        return self._instance
