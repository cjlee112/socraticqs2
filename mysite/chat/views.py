import injections
import logging
from django.db.models import Q
from django.views.generic import View
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from chat.services import LiveChatFsmHandler
from chat.utils import enroll_generator
from fsm.models import FSMState

from .models import Chat, EnrollUnitCode
from .services import ProgressHandler
from ct.models import Unit, Role, UnitLesson, ConceptLink, CourseUnit


@injections.has
class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)

    def get_enroll_code_object(self, enroll_key):
        """
        Return EnrollUnitCode object
        :param enroll_key: enroll code
        :return: EnrollUnitCode instance
        """
        return get_object_or_404(EnrollUnitCode, enrollCode=enroll_key)

    @method_decorator(login_required)
    def get(self, request, enroll_key):
        enroll_code = self.get_enroll_code_object(enroll_key)
        courseUnit = enroll_code.courseUnit
        unit = courseUnit.unit
        if not unit.unitlesson_set.filter(order__isnull=False).exists():
            return render(
                request,
                'lti/error.html',
                {'message': 'There are no Lessons to display for that Courselet.'}
            )
        if (
            not courseUnit.is_published() and
            not User.objects.filter(
                id=request.user.id,
                role__role=Role.INSTRUCTOR,
                role__course=courseUnit.course
            ).exists()
        ):
            return render(
                request,
                'lti/error.html',
                {'message': 'This Courselet is not published yet.'}
            )
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
                enroll_code=enroll_code,
                instructor=courseUnit.course.addedBy
            )
            chat.save(request)
        if chat.message_set.count() == 0:
            next_point = self.next_handler.start_point(unit=unit, chat=chat, request=request)
        else:
            next_point = chat.next_point

        lessons = unit.get_exercises()

        will_learn = set()
        need_to_know = set()
        for unit_lesson in unit.get_exercises():
            # QuerySet for "You will learn" and "Need to know" section
            containers_with_querysets = (
                (will_learn, ConceptLink.objects.filter(
                    Q(lesson=unit_lesson.lesson),
                    (Q(relationship=ConceptLink.DEFINES) | Q(relationship=ConceptLink.TESTS))
                )),
                (need_to_know, ConceptLink.objects.filter(
                    lesson=unit_lesson.lesson, relationship=ConceptLink.ASSUMES
                ))
            )
            for contaner, qs in containers_with_querysets:
                for concept_link in qs:
                    title = concept_link.concept.title
                    if concept_link.lesson.url:
                        url = concept_link.lesson.url
                    else:
                        ul = UnitLesson.objects.filter(
                            lesson__concept=concept_link.concept
                        ).values('id').first()
                        if ul:
                            url = reverse(
                                'ct:study_concept', args=(courseUnit.course.id, unit.id, ul['id'])
                            )
                    if url:
                        contaner.add((title, url))

        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'course': courseUnit.course,
                'unit': unit,
                'img_url': unit.img_url,
                'small_img_url': unit.small_img_url,
                'will_learn': will_learn,
                'need_to_know': need_to_know,
                'chat_id': chat.id,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'next_point': next_point,
                'fsmstate': chat.state,
            }
        )

class InitializeLiveSession(ChatInitialView):
    '''
    Entry point for live session chat.
    '''
    next_handler = LiveChatFsmHandler()


    def get_enroll_code_object(self, enroll_key):
        """
        Return EnrollUnitCode object
        :param enroll_key: enroll code
        :return: EnrollUnitCode instance
        """
        return get_object_or_404(EnrollUnitCode, enrollCode=enroll_key, isLive=True)

    def get(self, request, **kwargs):
        '''
        This method do init of live_chat FSM and return context needed to build chat on front end.
        :param request: django request.
        :param chat_id: chat id
        :return: rendered template with proper context.
        '''
        if 'enroll_key' in kwargs:
            return super(InitializeLiveSession, self).get(request, kwargs['enroll_key'])

        if 'state_id' in kwargs:
            # create new enroll code nad bind it to UL.
            # thin just redirect user to this page again
            state = get_object_or_404(FSMState, id=kwargs['state_id'], isLiveSession=True)
            data = state.get_all_state_data()
            course, unit = data['course'], data['unit']
            course_unit = CourseUnit.objects.filter(unit=data['unit'], course=data['course']).first()
            enroll = EnrollUnitCode.get_code_for_user_chat(
                is_live=True, course_unit=course_unit, user=request.user,
            )
            if not enroll.id:
                enroll.enrollCode = EnrollUnitCode.get_code(course_unit, isLive=True)
                enroll.save()


        # import ipdb; ipdb.set_trace()
        state = get_object_or_404(FSMState, id=kwargs.get('state_id'), isLiveSession=True)
        data = state.get_all_state_data()
        course, unit = data['course'], data['unit']
        course_unit = CourseUnit.objects.filter(unit=data['unit'], course=data['course']).first()

        if (
            not course_unit.is_published() and
            not User.objects.filter(
                id=request.user.id,
                role__role=Role.INSTRUCTOR,
                role__course=course_unit.course
            ).exists()
        ):
            return render(
                request,
                'lti/error.html',
                {'message': 'This Courselet is not published yet.'}
            )
        #
        # enroll, cr = EnrollUnitCode.objects.get_or_create(isLive=True, courseUnit=course_unit)
        # if cr:
        #     enroll.enrollCode = EnrollUnitCode.get_code(course_unit, isLive=True)
        #     enroll.save()

        chat = Chat.objects.filter(user=request.user, is_live=True, state__linkState=state).first()

        if not chat and state:
            chat = Chat(
                user=request.user,
                instructor=course_unit.course.addedBy,
                is_live=True,
                enroll_code=enroll
            )
            chat.save(request)

        if chat.message_set.count() == 0:
            next_point = self.next_handler.start_point(
                unit=unit, chat=chat, request=request,
                linkState=state, courseUnit=course_unit
            )
        else:
            next_point = chat.next_point

        lessons = unit.get_exercises()

        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'course': course_unit.course,
                'unit': unit,
                'img_url': unit.img_url,
                'small_img_url': unit.small_img_url,
                # 'will_learn': will_learn,
                # 'need_to_know': need_to_know,
                'chat_id': chat.id,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'next_point': next_point,
                'fsmstate': chat.state,
            }
        )