from django.contrib.auth.models import User

from ct.models import Lesson


class QuestionProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def get_question(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._data.get("question", ""),
            "kind": Lesson.ORCT_QUESTION,
            "addedBy": author or self._unit.addedBy,
        }
        question = Lesson(
            title=_converted['title'],
            text=_converted['text'],
            kind=_converted['kind'],
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
