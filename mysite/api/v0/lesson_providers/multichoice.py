from django.contrib.auth.models import User

from ct.models import Lesson


class MultiChoiceProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def _convert_data(self):
        correct_text = f"{self._data['question']}\r\n\r\n[choices]\r\n"

        for choice in self._data["choices"]:
            if choice['correct']:
                correct_text += "(*) " + choice['text'] + f"\r\n{self._data['answer']}\r\n"
            else:
                correct_text += "() " + choice['text'] + "\r\n"

        return correct_text

    def get_question(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._convert_data(),
            "kind": Lesson.ORCT_QUESTION,
            "addedBy": author or self._unit.addedBy,
        }
        question = Lesson(
            title=_converted['title'],
            text=_converted['text'],
            kind=_converted['kind'],
            sub_kind=Lesson.MULTIPLE_CHOICES,
            addedBy=_converted['addedBy'],
            treeID=1)
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
