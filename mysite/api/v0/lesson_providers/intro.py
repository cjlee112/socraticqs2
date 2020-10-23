from django.contrib.auth.models import User

from ct.models import Lesson


class IntroProvider:
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def get_intro(self):
        author = User.objects.filter(username=self._data.get("author")).first()

        _converted = {
            "title": self._data.get("title", ""),
            "text": self._data.get("message", ""),
            "kind": Lesson.BASE_EXPLANATION,
            "addedBy": author or self._unit.addedBy,
        }
        intro = Lesson(
            title=_converted['title'],
            text=_converted['text'],
            kind=_converted['kind'],
            addedBy=_converted['addedBy'],
            treeID=1)
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
