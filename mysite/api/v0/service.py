from api.v0.utils import ObjectFactory
from api.v0.lesson_providers.multichoice import MultiChoiceProviderBuilder
from api.v0.lesson_providers.intro import IntroProviderBuilder
from api.v0.lesson_providers.question import QuestionProviderBuilder
from api.v0.lesson_providers.canvas import CanvasProviderBuilder
from api.v0.lesson_providers.cfg import Provider


class LessonProvider(ObjectFactory):
    def get(self, provider_id, **kwargs):
        return self.create(provider_id, **kwargs)


factory = LessonProvider()
factory.register_builder(Provider.MULTICHOICE, MultiChoiceProviderBuilder())
factory.register_builder(Provider.INTRO, IntroProviderBuilder())
factory.register_builder(Provider.QUESTION, QuestionProviderBuilder())
factory.register_builder(Provider.CANVAS, CanvasProviderBuilder())
