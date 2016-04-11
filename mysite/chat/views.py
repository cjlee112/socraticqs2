import injections
from django.db.models import Q
from django.views.generic import View
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Chat, EnrollUnitCode
from .services import ProgressHandler
from ct.models import Unit, Role, UnitLesson, ConceptLink, ConceptGraph


@injections.has
class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)

    @method_decorator(login_required)
    def get(self, request, enroll_key):
        enroll_code = get_object_or_404(EnrollUnitCode, enrollCode=enroll_key)
        courseUnit = enroll_code.courseUnit
        unit = courseUnit.unit
        if not Role.objects.filter(
            user=request.user.id, course=courseUnit.course, role=Role.ENROLLED
        ):
            enrolling = Role.objects.get_or_create(user=request.user,
                                                   course=courseUnit.course,
                                                   role=Role.SELFSTUDY)[0]
            enrolling.role = Role.ENROLLED
            enrolling.save()

        chat = Chat.objects.filter(enroll_code=enroll_code, user=request.user).first()
        if not chat and enroll_key:
            chat = Chat(
                user=request.user,
                enroll_code=enroll_code
            )
            chat.save(request)
        if chat.message_set.count() == 0:
            next_point = self.next_handler.start_point(unit=unit, chat=chat, request=request)
        else:
            next_point = chat.next_point

        lessons = unit.get_exercises()

        concepts = set()
        will_learn = set()
        for unit_lesson in unit.get_exercises():
            for concept_link in ConceptLink.objects.filter(
                Q(lesson=unit_lesson.lesson),
                (Q(relationship=ConceptLink.DEFINES) | Q(relationship=ConceptLink.TESTS))
            ):
                title = concept_link.concept.title
                if concept_link.lesson.url:
                    url = concept_link.lesson.url
                else:
                    try:
                        ul = UnitLesson.objects.get(lesson__concept=concept_link.concept)
                    except UnitLesson.DoesNotExist:
                        raise Http404
                    url = reverse(
                        'ct:study_concept', args=(courseUnit.course.id, unit.id, ul.id)
                    )
                concepts.add(concept_link.concept)
                will_learn.add((title, url))

        need_to_know = set()
        for concept in concepts:
            for concept_graph in ConceptGraph.objects.filter(
                fromConcept=concept, relationship=ConceptGraph.DEPENDS
            ):
                title = concept_graph.toConcept.title
                unit_lesson = UnitLesson.objects.filter(
                    lesson__concept=concept_graph.toConcept
                ).first()
                if unit_lesson.lesson.url:
                    url = unit_lesson.lesson.url
                else:
                    url = reverse(
                        'ct:study_concept', args=(courseUnit.course.id, unit.id, unit_lesson.id)
                    )
                need_to_know.add((title, url))

        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'course': courseUnit.course,
                'unit': unit,
                'img_url': unit.img_url,
                'will_learn': will_learn,
                'need_to_know': need_to_know,
                'chat_id': chat.id,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'next_point': next_point,
                'fsmstate': chat.state
            }
        )
