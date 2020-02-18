import random

import waffle
import injections
from django.db.models.expressions import When, Case
from django.db.models.fields import IntegerField
from django.db.models import Q
from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.models import User

from mysite.mixins import LoginRequiredMixin
from ct.models import Role, UnitLesson, ConceptLink, CourseUnit, NEED_HELP_STATUS, NEED_REVIEW_STATUS
from chat.models import Message
from chat.services import LiveChatFsmHandler, ChatPreviewFsmHandler
from fsm.models import FSMState
from .models import Chat, EnrollUnitCode
from .services import ProgressHandler
from .utils import get_updated_thread_id

@injections.has
class ChatInitialView(LoginRequiredMixin, View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)
    template_name = 'chat/main_view.html'
    tester_mode = False

    @staticmethod
    def get_back_url(*args, **kwargs):
        """
        Return link to back page - by default - lms course page.
        """
        return "Course", reverse('lms:course_view', kwargs=dict(course_id=kwargs['courseUnit'].course.id))

    @staticmethod
    def get_enroll_code_object(enroll_key):
        """
        Return EnrollUnitCode object.

        :param enroll_key: enroll code
        :return: EnrollUnitCode instance
        """
        return get_object_or_404(EnrollUnitCode, enrollCode=enroll_key, isPreview=False)

    @staticmethod
    def get_will_learn_need_know(unit, courseUnit):
        """
        Steps to define Concepts for Will learn and Need to know:

            `/ct/teach/courses/:id/units/:id/`
            `/ct/teach/courses/:id/units/:id/lessons/`
            `/ct/teach/courses/:id/units/:id/lessons/:id/`
            `/ct/teach/courses/:id/units/:id/lessons/:id/concepts/`

        `Will learn`

            * We want all Concepts that Defines or Tests Understanding of Lesson
            * Choose Defines or Test for Concept

        `Need to know`

            * We want all Concepts that Assumes a Lesson
            * Choose Assumes for Concept
        """
        will_learn = set()
        need_to_know = set()
        for unit_lesson in unit.get_exercises():
            # QuerySet for "You will learn" and "Need to know" section
            containers_with_querysets = (
                (will_learn, ConceptLink.objects.filter(
                    Q(lesson=unit_lesson.lesson),
                    (Q(relationship=ConceptLink.DEFINES) | Q(relationship=ConceptLink.TESTS)))
                 if unit_lesson.unit.is_show_will_learn else ()),
                (need_to_know, ConceptLink.objects.filter(
                    lesson=unit_lesson.lesson, relationship=ConceptLink.ASSUMES))
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
        return will_learn, need_to_know

    def get_or_init_chat(self, enroll_code, chat_id):
        """Get chat by id.

        Logic of this method is:
         * try to cast recieved ID to int
         * if gets an error while casting:
           * set i_chat_id = 0 if ValueError
           * set i_chat_id = None if TypeError
         * if i_chat_id:
           * try to get chat by id
         * if i_chat_id is None:
           * restore last session
         * if i_chat_id == 0:
           * create new chat
        :return i_chat_id and chat
        """
        chat = None
        courseUnit = enroll_code.courseUnit
        try:
            # try to convert chat_id to int
            i_chat_id = int(chat_id)
        except ValueError:
            # if error - set i_chat_id to zero - it means create new chat
            i_chat_id = 0
        except TypeError:
            i_chat_id = None

        if i_chat_id:  # chat_id is passed - restore chat by id
            chat = self.get_chat(self.request, enroll_code, user=self.request.user, id=i_chat_id)
        elif i_chat_id is None:  # chat_id not passed - restore last session
            chat = self.get_chat(self.request, enroll_code, user=self.request.user)
        elif i_chat_id == 0 and enroll_code:  # create new session
            chat = self.create_new_chat(self.request, enroll_code, courseUnit)

        if chat and not chat.state:
            chat.next_point = None
            chat.save()

        return chat, i_chat_id

    @staticmethod
    def check_course_not_published_and_user_is_not_instructor(request, courseUnit):
        """
        This method checks that course is not published and user is not instructor.

        :param request: request
        :param courseUnit: course unit
        :return: True | False
        """
        return (
            not courseUnit.is_published() and
            not User.objects.filter(
                id=request.user.id,
                role__role=Role.INSTRUCTOR,
                role__course=courseUnit.course
            ).exists()
        )

    @staticmethod
    def user_enrolled(request, courseUnit):
        return Role.objects.filter(
            user=request.user.id, course=courseUnit.course, role=Role.ENROLLED
        )

    def create_new_chat(self, request, enroll_code, courseUnit, **kwargs):
        # TODO user_trial_mode = self.define_user_trial_mode(request, courseUnit)
        defaults = dict(
            user=request.user,
            enroll_code=enroll_code,
            instructor=courseUnit.course.addedBy,
            is_preview=False,
            is_trial=False
        )
        defaults.update(kwargs)
        chat = Chat(**defaults)
        chat.save()
        return chat

    def define_user_trial_mode(self, request, course_unit):
        """
        Define trial mode for enrolled user depending on course's trial mode settings
        If mode still is undefined get percent of user's trial mode
         and if count of them is less than 50% set trial mode randomly,
        Arguments:
            request (obj): Django Request
            course_unit (obj): Model object
        Return (bool): Existing or newly added trial mode
        """
        user = request.user
        user_enrolled = self.user_enrolled(request, course_unit).first()
        trial_mode = False
        if user_enrolled:  # if user's role exists
            # course is trial and role.trial_mode has been set
            if course_unit.course.trial and user_enrolled.trial_mode is None:
                # get users enrolled to this course
                enrolled_users = Role.objects.filter(
                    course_id=course_unit.course.id,
                    role=Role.ENROLLED
                )
                # count the percent of users in trial mode
                trial_mode_prsnt = float(enrolled_users.filter(trial_mode=True).count()) / enrolled_users.count() * 100
                roles_to_update = Role.objects.filter(
                      user=user.id, role__in=[Role.ENROLLED, Role.SELFSTUDY], course_id=course_unit.course.id)
                # if the percent is not exceeded get random value for trial mode
                if trial_mode_prsnt < 50:  # hardcoded but can be implemented for adjusting from admin
                    trial_mode = random.choice([True, False])
                roles_to_update.update(trial_mode=trial_mode)
            else:
                trial_mode = bool(user_enrolled.trial_mode)  # course is not trial or role has already been set
        return trial_mode

    @staticmethod
    def check_unitlessons_with_order_null_exists(unit):
        return unit.unitlesson_set.filter(order__isnull=False).exists()

    @staticmethod
    def get_chat(request, enroll_code, **kwargs):
        kw = dict(
            enroll_code=enroll_code, user=request.user,
        )
        kw.update(kwargs)
        return Chat.objects.filter(**kw).first()

    def get_chat_sessions(self, request, enroll_code, courseUnit):
        return Chat.objects.filter(
            enroll_code=enroll_code,
            user=request.user,
            instructor=courseUnit.course.addedBy,
            is_live=False,
            is_test=self.tester_mode,
            is_preview=False
        ).annotate(
            not_finished=Case(
                When(state_id__isnull=True, then=0),
                When(state_id__isnull=False, then=1),
                default=0,
                output_field=IntegerField())
        ).order_by('-not_finished', '-last_modify_timestamp')

    def get(self, request, enroll_key, chat_id=None):
        enroll_code = self.get_enroll_code_object(enroll_key)
        courseUnit = enroll_code.courseUnit
        unit = courseUnit.unit
        if not self.check_unitlessons_with_order_null_exists(unit):
            return render(
                request,
                'lti/error.html',
                {'message': 'There are no Lessons to display for that Courselet.'}
            )
        if self.check_course_not_published_and_user_is_not_instructor(request, courseUnit):
            return render(
                request,
                'lti/error.html',
                {'message': 'This Courselet is not published yet or you have no permisions to open it.'}
            )
        if not self.user_enrolled(request, courseUnit):
            enrolling = Role.objects.get_or_create(user=request.user,
                                                   course=courseUnit.course,
                                                   role=Role.SELFSTUDY)[0]
            enrolling.role = Role.ENROLLED
            enrolling.save()

        # new chat will be created only if chat_id is 0
        chat, i_chat_id = self.get_or_init_chat(enroll_code, chat_id)
        lessons = unit.get_exercises()

        if chat and chat.is_live:
            lessons = Message.objects.filter(
                chat=chat,
                contenttype='unitlesson',
                kind='orct',
                type='message',
                owner=request.user,
            )

        will_learn, need_to_know = self.get_will_learn_need_know(unit, courseUnit)

        try:
            instructor_icon = courseUnit.course.addedBy.instructor.icon_url
        except AttributeError:
            instructor_icon = ''

        chat_sessions = self.get_chat_sessions(request, enroll_code, courseUnit)
        back_url_name, back_url = self.get_back_url(**locals())
        last_history = chat_sessions.filter(state__isnull=True, progress=100).order_by('id').last()
        updated_thread_id = None


        if last_history:
            updated_thread_id = get_updated_thread_id(last_history)

        return render(
            request,
            self.template_name,
            {
                'chat_sessions_exists': len(chat_sessions),  # mark for frontend
                'chat_sessions': chat_sessions,  # .exclude(id=chat.id), # TODO: UNCOMMENT this line to exclude current chat from sessions
                'most_recent_complete_session': last_history,
                'updated_thread_id': updated_thread_id or -1,
                'chat': chat,
                'chat_id': i_chat_id,
                'course': courseUnit.course,
                'instructor_icon': instructor_icon,
                'unit': unit,
                'img_url': unit.img_url,
                'small_img_url': unit.small_img_url,
                'will_learn': will_learn,
                'need_to_know': need_to_know,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'fsmstate': chat.state if chat else None,
                'enroll_code': enroll_key,
                # 'next_point': next_point,
                'back_url': back_url,
                'back_url_name': back_url_name
            }
        )


class ChatNoJSInit(object):
    """
    Implement basic chat initialization process (no JS required).
    """

    def get_or_init_chat(self, enroll_code, chat_id):
        """
        Logic of creating new chat is:

        * check chat_id
            * if chat_it is present:
                * get_chat by id, enroll_code, user
            * if no chat_id
                * get chat by fsmName, enroll_code, user
         * if chat waws found
            * if exist - return it
            * if not exist - create new one
        * check messages count in this Chat
            * if 0 - call to self.next_handler.start_point(
        * check chat.state
            * if chat.state is None - set chat.next_point to None and save chat.
        """
        if chat_id:
            chat = self.get_chat(
                self.request,
                enroll_code=enroll_code,
                id=chat_id
            )
        else:
            chat = self.get_chat(
                self.request,
                enroll_code,
                **{'state__fsmNode__fsm__name': self.next_handler.FMS_name}
            )
        if not chat and enroll_code:
            chat = self.create_new_chat(
                self.request,
                enroll_code,
                enroll_code.courseUnit
            )
        if chat.message_set.count() == 0:
            self.next_handler.start_point(
                unit=enroll_code.courseUnit.unit,
                chat=chat,
                request=self.request
            )
        elif not chat.state:
            next_point = None
            chat.next_point = next_point
            chat.save()
        return chat, chat_id


class CourseletPreviewView(ChatInitialView):
    next_handler = ChatPreviewFsmHandler()

    @staticmethod
    def get_back_url(*args, **kwargs):
        """
        Return back url - ctms course page.
        """
        return "Return", reverse(
            'ctms:courslet_view',
            kwargs=dict(
                course_pk=kwargs['courseUnit'].course.id,
                pk=kwargs['courseUnit'].pk)
        )

    @staticmethod
    def get_enroll_code_object(enroll_key):
        """
        Return EnrollUnitCode object.

        :param enroll_key: enroll code
        :return: EnrollUnitCode instance
        """
        return get_object_or_404(EnrollUnitCode, enrollCode=enroll_key, isPreview=True)

    def create_new_chat(self, request, enroll_code, courseUnit, **kwargs):
        return super(CourseletPreviewView, self).create_new_chat(
            request=request,
            courseUnit=courseUnit,
            user=request.user,
            enroll_code=enroll_code,
            instructor=courseUnit.course.addedBy,
            is_preview=True
        )

    @staticmethod
    def check_course_not_published_and_user_is_not_instructor(request, courseUnit):
        """
        Check that course is not published and user is not instructor.

        :param request: request
        :param courseUnit: course unit
        :return: True | False
        """
        return (
            not courseUnit.addedBy == request.user and
            not User.objects.filter(
                id=request.user.id, role__role=Role.INSTRUCTOR, role__course=courseUnit.course
            ).exists()
        )

    @staticmethod
    def get_chat(request, enroll_code, **kwargs):
        return ChatInitialView.get_chat(request, enroll_code, is_preview=True)

    def get(self, request, enroll_key):
        request.user.fsmstate_set.filter(chat__is_preview=True).delete()
        request.user.chat_set.filter(is_preview=True).update(enroll_code=None)
        return super(CourseletPreviewView, self).get(request, enroll_key)


class InitializeLiveSession(ChatInitialView):
    """
    Entry point for live session chat.

    Check that user is authenticated and create a chat for him.
    """
    next_handler = LiveChatFsmHandler()

    @staticmethod
    def get_enroll_code_object(enroll_key):
        """
        Return EnrollUnitCode object

        :param enroll_key: enroll code
        :return: EnrollUnitCode instance
        """
        return get_object_or_404(EnrollUnitCode, enrollCode=enroll_key, isLive=True, chat__is_preview=False)

    def get(self, request, **kwargs):
        '''
        Do init of live_chat FSM and return context needed to build chat on front end.

        :param request: django request.
        :param chat_id: chat id
        :return: rendered template with proper context.
        '''
        if not waffle.switch_is_active('live_session_enabled'):
            return render(
                request,
                'lti/error.html',
                {'message': 'This action is not allowed now.'}
            )
        if 'enroll_key' in kwargs:
            return super(InitializeLiveSession, self).get(request, kwargs['enroll_key'])

        if 'state_id' in kwargs:
            # create new enroll code and bind it to UL.
            # thin just redirect user to this page again
            state = get_object_or_404(FSMState, id=kwargs['state_id'], isLiveSession=True)
            data = state.get_all_state_data()
            course, unit = data['course'], data['unit']
            course_unit = CourseUnit.objects.filter(unit=data['unit'], course=data['course']).first()

        if not unit.unitlesson_set.filter(order__isnull=False).exists():
            return render(
                request,
                'lti/error.html',
                {'message': 'There are no Lessons to display for that Courselet.'}
            )
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
        if not Role.objects.filter(
            user=request.user.id, course=course_unit.course, role=Role.ENROLLED
        ):
            enrolling = Role.objects.get_or_create(user=request.user,
                                                   course=course_unit.course,
                                                   role=Role.SELFSTUDY)[0]
            enrolling.role = Role.ENROLLED
            enrolling.save()

        chat = Chat.objects.filter(user=request.user, is_live=True, state__linkState=state).first()

        if not chat and state:
            enroll_code = EnrollUnitCode.objects.create(courseUnit=course_unit, isLive=True)
            chat = Chat(
                user=request.user,
                instructor=course_unit.course.addedBy,
                is_live=True,
                enroll_code=enroll_code,
                is_preview=False
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

        will_learn, need_to_know = self.get_will_learn_need_know(unit, course_unit)

        try:
            instructor_icon = course_unit.course.addedBy.instructor.icon_url
        except AttributeError:
            instructor_icon = ''

        back_url_name, back_url = self.get_back_url(courseUnit=locals().get('course_unit'))
        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'chat': chat,
                'course': course_unit.course,
                'instructor_icon': instructor_icon,
                'unit': unit,
                'img_url': unit.img_url,
                'small_img_url': unit.small_img_url,
                'will_learn': will_learn,
                'need_to_know': need_to_know,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'next_point': next_point,
                'fsmstate': chat.state,
                'back_url': back_url,
                'back_url_name': back_url_name,
            }
        )


class CheckChatInitialView(ChatInitialView):
    tester_mode = True

    def create_new_chat(self, request, enroll_code, courseUnit, **kwargs):
        return super(CheckChatInitialView, self).create_new_chat(
            request=request,
            courseUnit=courseUnit,
            user=request.user,
            enroll_code=enroll_code,
            instructor=courseUnit.course.addedBy,
            is_test=True
        )

    @staticmethod
    def get_back_url(*args, **kwargs):
        """
        Return back_url_name and back_url
        """

        return "Return", reverse('lms:tester_course_view', kwargs=dict(course_id=kwargs['courseUnit'].course.id))

    @staticmethod
    def check_course_not_published_and_user_is_not_instructor(request, courseUnit):
        return not courseUnit.course.invite_set.filter(
            Q(user=request.user) | Q(email=request.user.email),
        ) and not User.objects.filter(
            id=request.user.id,
            role__role=Role.INSTRUCTOR,
            role__course=courseUnit.course
        ).exists()
