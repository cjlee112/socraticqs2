import base64
import secrets

from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from ct.models import Lesson


class SubKindBaseProvider:
    KIND = Lesson.ORCT_QUESTION
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit
        self._response = {}

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
        out = {}
        if 'data' in self._data:   # let caller save JSON directly into Lesson.data
            out['data'] = self._data['data']
        if 'text2html' in self._data:   # let caller save JSON directly into Lesson.text2html
            out['text2html'] = self._data['text2html']
        if 'image' in self._data:  # Generate an Image attachment based on base64 data.
            out['attachment'] = ContentFile(base64.b64decode(self._data["image"]),
                                            name=f"multichoice_image_{secrets.token_hex(15)}.jpg")
        return out


    def extra_answer(self):
        """
        Return any required additional fields for a Lesson.

        This can be used to override any fields indended to be
        added to a answer Lesson instance.
        """
        out = {}
        if 'answerImg' in self._data:  # Generate an Image attachment based on base64 data.
            out['attachment'] = ContentFile(base64.b64decode(self._data["answerImg"]),
                                            name=f"multichoice_answer_image_{secrets.token_hex(15)}.jpg")
        return out

    def get_question(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._convert_data(),
            "kind": self.KIND,
            "sub_kind": self.SUB_KIND,
            "addedBy": author or self._unit.addedBy,
        }
        _converted.update(self.extra())

        question = Lesson(**_converted)
        question.save_root()

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
        answer.save_root()

        return answer


class MultiChoiceProvider(SubKindBaseProvider):
    KIND = Lesson.ASSESSMENT
    SUB_KIND = Lesson.MULTIPLE_CHOICES
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
