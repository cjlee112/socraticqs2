"""
Module implements conversion functions for the Lesson object.
"""

from django.contrib.auth.models import User

from ct.models import UnitLesson, Lesson


class Creator:
    """
    Creates various parts of a Thread.

    This class is responsible for constructing all
    the parts for a Thread.
    """
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit

    def create(self):
        """
        Create.
        """
        pass

    def get_base(self):
        """
        Base method for base Lesson creation.
        """
        pass

    def get_answer(self):
        """
        Base method for answers Lesson creation.
        """
        pass


class IntroCreator(Creator):
    """
    Creates various parts of a Intro Thread.
    """
    def create(self):
        self.get_base()

    def get_base(self):
        """
        Create base Lesson
        """
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

        order = self._unit.next_order()
        unit_lesson = UnitLesson(
            unit=self._unit, lesson=intro, addedBy=_converted['addedBy'],
            treeID=intro.treeID, order=order, kind=UnitLesson.COMPONENT)
        unit_lesson.save()

        self._thread = unit_lesson


class QuestionCreator(Creator):
    """
    Creates various parts of a Question Thread.
    """
    def create(self):
        self.get_base()
        self.set_answer()

    def get_base(self):
        """
        Create base Lesson.
        """
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

        order = self._unit.next_order()
        unit_lesson = UnitLesson(
            unit=self._unit, lesson=question, addedBy=_converted['addedBy'],
            treeID=question.treeID, order=order, kind=UnitLesson.COMPONENT)
        unit_lesson.save()

        self._thread = unit_lesson

    def set_answer(self):
        """
        Create answer Lesson.
        """
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

        self._thread._answer = UnitLesson(
            lesson=answer,
            unit=self._unit,
            kind=UnitLesson.ANSWERS,
            addedBy=_converted['addedBy'],
            treeID=1,
            parent=self._thread)
        self._thread._answer.save()


class ThreadBuilder:
    def __init__(self, unit):
        self._unit = unit

    def build(self, data):
        switch = {
            "intro": IntroCreator,
            "question": QuestionCreator,
        }

        creator = switch.get(data.get("kind", "intro"))(data, self._unit)
        creator.create()

        return creator._thread
