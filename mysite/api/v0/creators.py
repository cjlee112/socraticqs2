"""
Module implements conversion functions for the Lesson object.
"""

from django.contrib.auth.models import User

from ct.models import UnitLesson, Lesson

from .service import factory
from .lesson_providers.cfg import Provider


# TODO: get rid of this
mapping = {
    "question": Provider.QUESTION,
    "multichoice": Provider.MULTICHOICE,
    "intro": Provider.INTRO,
    "canvas": Provider.CANVAS
}


class Creator:
    """
    Creates various parts of a Thread.

    This class is responsible for constructing all
    the parts for a Thread.
    """
    def __init__(self, data, unit):
        self._data = data
        self._unit = unit
        _provider_id = mapping.get(data["kind"])
        self._lesson_provider = factory.get(_provider_id, data=data, unit=unit)

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
        intro = self._lesson_provider.get_intro()

        order = self._unit.next_order()
        unit_lesson = UnitLesson(
            unit=self._unit, lesson=intro, addedBy=intro.addedBy,
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
        question = self._lesson_provider.get_question()

        order = self._unit.next_order()
        unit_lesson = UnitLesson(
            unit=self._unit, lesson=question, addedBy=question.addedBy,
            treeID=question.treeID, order=order, kind=UnitLesson.COMPONENT)
        unit_lesson.save()

        self._thread = unit_lesson

    def set_answer(self):
        """
        Create answer Lesson.
        """
        answer = self._lesson_provider.get_answer()

        self._thread._answer = UnitLesson(
            lesson=answer,
            unit=self._unit,
            kind=UnitLesson.ANSWERS,
            addedBy=answer.addedBy,
            treeID=1,
            parent=self._thread)
        self._thread._answer.save()


class MultichoiceCreator(QuestionCreator):
    pass


class ThreadBuilder:
    def __init__(self, unit):
        self._unit = unit

    def build(self, data):
        switch = {
            "intro": IntroCreator,
            "question": QuestionCreator,
            "multichoice": MultichoiceCreator,
        }

        creator = switch.get(data.get("kind", "intro"))(data, self._unit)
        creator.create()

        return creator._thread
