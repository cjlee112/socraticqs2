from django.test import TestCase

from ct.models import Response, UnitLesson
from grading.models import CorrectnessMeter


class BaseGraderTests(TestCase):
    def test_search_graders(self):
        """Test that discovering graders works properly."""
        from base_grader import GRADERS
        self.assertIn('numbers', GRADERS)
        # base grader should not be included
        self.assertIsNone(GRADERS.get('base'))


class NumbersGraderTest(TestCase):
    fixtures = ["chat/tests/fixtures/initial_numbers.json"]

    def setUp(self):
        from base_grader import GRADERS
        self.unitLesson = UnitLesson.objects.get(lesson__id=110)
        self.answer = self.unitLesson.get_answers()[0]
        self.responses = Response.objects.filter(unitLesson=self.unitLesson)
        CorrectnessMeter.objects.all().delete()
        self.GraderCls = GRADERS.get(self.unitLesson.sub_kind)

    def test_correct_numbers_grading(self):
        cor_met_count = CorrectnessMeter.objects.all().count()

        # create partially correct answer
        response = self.responses[0]
        response.text = 11.0
        response.save()

        grader = self.GraderCls(self.unitLesson, response)
        self.assertEqual(grader.grade, 1)
        self.assertEqual(grader.is_correct, True)
        self.assertEqual(CorrectnessMeter.objects.all().count(), cor_met_count + 1)
        self.assertEqual(grader.message, u"correct")

        cor_met = CorrectnessMeter.objects.get()
        self.assertEqual(cor_met.correctness, CorrectnessMeter.CORRECT)
        self.assertEqual(cor_met.points, CorrectnessMeter.CORRECT_ANSWER_POINTS)

    def test_not_correct_numbers_grading(self):
        cor_met_count = CorrectnessMeter.objects.all().count()

        # create partially correct answer
        response = self.responses[0]
        response.text = 1000.0
        response.save()

        grader = self.GraderCls(self.unitLesson, response)
        self.assertEqual(grader.grade, 0)
        self.assertEqual(grader.is_correct, False)
        self.assertEqual(CorrectnessMeter.objects.all().count(), cor_met_count + 1)
        self.assertEqual(grader.message, u"not correct")

        cor_met = CorrectnessMeter.objects.get()
        self.assertEqual(cor_met.correctness, CorrectnessMeter.NOT_CORRECT)
        self.assertEqual(cor_met.points, CorrectnessMeter.NOT_CORRECT_ANSWER_POINTS)

    def test_partially_correct_numbers_grading(self):
        cor_met_count = CorrectnessMeter.objects.all().count()

        # create partially correct answer
        response = self.responses[0]
        response.text = 100.0
        response.save()

        grader = self.GraderCls(self.unitLesson, response)
        self.assertEqual(grader.grade, 0.9)
        self.assertEqual(grader.is_correct, True)
        self.assertEqual(CorrectnessMeter.objects.all().count(), cor_met_count + 1)
        self.assertEqual(grader.message, u"partially correct")

        cor_met = CorrectnessMeter.objects.get()
        self.assertEqual(cor_met.correctness, CorrectnessMeter.PARTIALLY_CORRECT)
        self.assertEqual(
            cor_met.points,
            CorrectnessMeter.CORRECT_ANSWER_POINTS * CorrectnessMeter.PARTIALLY_CORRECT_ANSWER_POINT_REDUCTION
        )
