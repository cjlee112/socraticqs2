from ct.load_json import get_or_create_user
from grading.base_grader import BaseGrader
from grading.models import CorrectnessMeter


class EquationGrader(BaseGrader):
    """
    Grader for numbers.
    """
    grading_type = 'equation'

    def convert_recieved_value(self, value):
        return " ".join(value.strip().split())

    def _is_correct(self, value):
        return self.convert_recieved_value(self.first_answer.lesson.text) == value

    def update_correctness_meter(self, value):
        """Update CorrectMeter model for user.

        :param correctnes: {correct, not_correct} = {1, 0}
        :return None
        """
        if self.is_correct:
            correctness = CorrectnessMeter.CORRECT
            points = CorrectnessMeter.CORRECT_ANSWER_POINTS
        else:
            correctness = CorrectnessMeter.NOT_CORRECT
            points = CorrectnessMeter.NOT_CORRECT_ANSWER_POINTS
        cor_meter = CorrectnessMeter.objects.create(response=self.response, points=points, correctness=correctness)
        return cor_meter

    @property
    def message(self):
        return self.cor_meter.get_correctness_display()

    def _grade(self, value):
        """
        Return grade based on user response.

        Check that user input was the same as answer for the question.
        :param value: current answer
        :return: grade (0 or 1)
        """
        self.cor_meter = self.update_correctness_meter(value)
        return self.cor_meter.points
