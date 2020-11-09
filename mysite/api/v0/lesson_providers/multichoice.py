import base64
import secrets

from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from ct.models import Lesson


class SubKindBaseProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def _convert_data(self):
        """
        Convert question data to a desired shape.
        """
        return self._data["question"]

    def extra(self):
        """
        Return any required additional fields for a Lesson.

        This can be used to override any fields indended to be
        added to a Lesson instance.
        """
        return {}

    def extra_answer(self):
        """
        Return any required additional fields for a Lesson.

        This can be used to override any fields indended to be
        added to a answer Lesson instance.
        """
        return {}

    def get_question(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._convert_data(),
            "kind": Lesson.ORCT_QUESTION,
            "sub_kind": self.SUB_KIND,
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
        _converted.update(self.extra_answer())

        answer = Lesson(**_converted)
        answer.save()

        return answer


class MultiChoiceProvider(SubKindBaseProvider):
    SUB_KIND = Lesson.MULTIPLE_CHOICES

    def extra(self):
        """
        Generate an Image attachment based on base64 data.

        API request data must contain `image` field with
        base64 encoded image.
        """
        if not self._data.get("image"):
            return {}

        _ext = "jpg"
        _attachment = ContentFile(
            base64.b64decode(self._data["image"]),
            name=f"multichoice_image_{secrets.token_hex(15)}." + _ext)

        return {
            "attachment": _attachment
        }

    def extra_answer(self):
        """
        Generate an Image attachment based on base64 data.

        API request data must contain `answerImg` field with
        base64 encoded image.
        """
        if not self._data.get("answerImg"):
            return {}

        _ext = "jpg"
        _attachment = ContentFile(
            base64.b64decode(self._data["answerImg"]),
            name=f"multichoice_answer_image_{secrets.token_hex(15)}." + _ext)

        return {
            "attachment": _attachment
        }

    def _convert_data(self):
        correct_text = f"{self._data['question']}\r\n\r\n[choices]\r\n"

        for choice in self._data["choices"]:
            img_tag = ""
            if choice.get("img"):
                img_tag = f' <img src="{choice.get("img")}">'

            if choice['correct']:
                correct_text += "(*) " + choice.get('text', '') + img_tag + \
                    f"\r\n{self._data['answer']}\r\n"
            else:
                correct_text += "() " + choice.get('text', '') + img_tag + "\r\n"

        return correct_text


class MultiChoiceProviderBuilder:
    """
    MultiChoiceProvider specific builder.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, data, unit, **_ignored):
        """
        Call authorize method, save client and return it.
        """
        self._instance = MultiChoiceProvider(data, unit)

        return self._instance
