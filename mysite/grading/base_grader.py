import glob
import importlib


GRADERS = {}

class KnowChildrenMeta(type):
    def __new__(cls, name, bases, dct):
        kls = super(KnowChildrenMeta, cls).__new__(cls, name, bases, dct)
        if hasattr(kls, 'grading_type'):
            GRADERS[kls.grading_type] = kls
        return kls


class BaseGrader(object):
    """
    Base grader class.
    """
    __metaclass__ = KnowChildrenMeta

    def __init__(self, unitlesson, response, *args, **kwargs):
        self.unitlesson = unitlesson
        self.answers = unitlesson.get_answers()
        self.response = response
        self.first_answer = self.answers[0] if len(self.answers) else None

    def _is_correct(self, val):
        """This Function should be defined in inherited class."""
        raise NotImplementedError()

    def _grade(self, val):
        """This Function should be defined in inherited class."""
        raise NotImplementedError()

    def convert_recieved_value(self, val):
        return val

    @property
    def grade(self):
        """Calculate grade to send to lti."""
        return self._grade(self.convert_recieved_value(self.response.text))

    @property
    def is_correct(self):
        """Check that answer is correct."""
        return self._is_correct(self.convert_recieved_value(self.response.text))


# hook to import all available graders to call their metaclass and insert them into GRADERS dict
ignore = ('base_grader.py',)
for modpath in glob.glob("*/*_grader.py"):
    splitted_path = modpath[:-3].split('/')
    if splitted_path[-1] not in ignore:

        mod = importlib.import_module(".".join(splitted_path))






