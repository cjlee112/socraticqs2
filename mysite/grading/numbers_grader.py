from ct.load_json import get_or_create_user
from grading.base_grader import BaseGrader
from grading.models import CorrectnessMeter


class NumberGrader(BaseGrader):
    """
    Grader for numbers.
    """
    grading_type = 'numbers'

    def __init__(self, unitlesson, response, *args, **kwargs):
        super(NumberGrader, self).__init__(unitlesson, response)
        self.min_val = self.unitlesson.lesson.number_min_value
        self.max_val = self.unitlesson.lesson.number_max_value
        self.precision = self.unitlesson.lesson.number_precision

    def convert_recieved_value(self, value):
        try:
            return float(value)
        except ValueError as e:
            raise e

    def _is_correct(self, value):
        return self.min_val - self.precision <= value <= self.max_val + self.precision

    def update_correctness_meter(self, value):
        """Update CorrectMeter model for user.

        :param correctnes: {correct, partially_correct}, str, all other values are represented as not_correct value.
        :return None
        """
        if self.is_correct:
            if self.min_val <= value <= self.max_val:
                correctness = CorrectnessMeter.CORRECT
                points = CorrectnessMeter.CORRECT_ANSER_POINTS
            else:
                correctness = CorrectnessMeter.PARTIALLY_CORRECT
                points = (
                    CorrectnessMeter.CORRECT_ANSER_POINTS * CorrectnessMeter.PARTIALLY_CORRECT_ANSWER_POINT_REDUCTION
                )
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

            Logic:
                * if min_val < value < vax_val - then grade = 1
                * if min_val - precision <= value <= max_val + precision - then grade = 0.9
                * if answer is not correct - then grade = 0
        :param value: current answer
        :return: float grade (0...1)
        """
        self.cor_meter = self.update_correctness_meter(value)
        return self.cor_meter.points
