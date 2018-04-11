from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count

from ct.models import Response


class CorrectnessMeter(models.Model):
    """User answers correctness meter."""
    PARTIALLY_CORRECT_ANSWER_POINT_REDUCTION = 0.9
    CORRECT_ANSWER_POINTS = 1
    NOT_CORRECT_ANSWER_POINTS = 0
    NOT_CORRECT = 'not_correct'
    CORRECT = 'correct'
    PARTIALLY_CORRECT = 'partially_correct'
    CORRECTNESS_CHOICES = (
        (CORRECT, 'Correct'),
        (PARTIALLY_CORRECT, 'Partially correct'),
        (NOT_CORRECT, 'Not correct'),
    )

    response = models.ForeignKey(Response)
    correctness = models.CharField(choices=CORRECTNESS_CHOICES, max_length=25)
    points = models.FloatField(default=0)

    @classmethod
    def get_user_answers_freq(cls, user, correctness=CORRECT):
        total_user_answers = CorrectnessMeter.objects.filter(response__author=user)
        try:
            return total_user_answers.filter(correctness=correctness).count() / float(total_user_answers.count())
        except ZeroDivisionError:
            return

    def __str__(self):
            return "{} {} {}".format(self.response.author, self.correctness, self.points)
