import base64
import secrets

from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from ct.models import Lesson


class QuestionProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def _convert_data(self):
        if "comparisons" not in self._data:
            return self._data.get("question", "")

        correct_text = f"{self._data['question']}\r\n\r\n"

        for choice in self._data["comparisons"]:
            correct_text += f"- {choice['text']}\r\n"

        return correct_text

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

    def get_question(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._convert_data(),
            "kind": Lesson.ORCT_QUESTION,
            "treeID": 1,
            "addedBy": author or self._unit.addedBy,
        }
        _converted.update(self.extra())

        question = Lesson(**_converted)
        question.save()

        return question

    def get_answer(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": "Answer",
            "text": self._data.get("answer", ""),
            "kind": Lesson.ANSWER,
            "addedBy": author or self._unit.addedBy,
        }
        answer = Lesson(
            title=_converted['title'],
            text=_converted['text'],
            kind=_converted['kind'],
            addedBy=_converted['addedBy'])
        answer.save()

        return answer


class QuestionProviderBuilder:
    """
    QuestionProvider specific builder.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, data, unit, **_ignored):
        """
        Call authorize method, save client and return it.
        """
        self._instance = QuestionProvider(data, unit)

        return self._instance
