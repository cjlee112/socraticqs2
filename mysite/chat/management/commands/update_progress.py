from functools import reduce

from django.core.management.base import BaseCommand

from chat.serializers import LessonSerializer
from chat.models import Chat


class Command(BaseCommand):
    """
    Update all Chats progress.
    """
    def handle(self, *args, **options):
        for chat in Chat.objects.all():
            messages = chat.message_set.filter(contenttype='chatdivider', is_additional=False)
            lessons = list(
                chat.enroll_code.courseUnit.unit.unitlesson_set.filter(
                    order__isnull=False
                ).order_by('order')
            )
            for each in messages:
                try:
                    if each.content.unitlesson in lessons:
                        lessons[lessons.index(each.content.unitlesson)].message = each.id
                    elif each.content.unitlesson and each.content.unitlesson.kind != 'answers':
                        lesson = each.content.unitlesson
                        lesson.message = each.id
                        lessons.append(lesson)
                except:
                    pass
            lessons_dict = LessonSerializer(many=True).to_representation(lessons)

            if lessons_dict and chat.state:
                done = reduce(lambda x, y: x+y, [x['isDone'] for x in lessons_dict])
                progress = round(float(done)/len(lessons_dict), 2)
            else:
                # if no lessons passed yet - return 1
                progress = 1

            if not chat.progress == (progress * 100):
                chat.progress = progress * 100
                chat.save()

        self.stdout.write('Updated.')
