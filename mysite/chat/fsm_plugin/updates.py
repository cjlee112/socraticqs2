from dateutil import tz
from functools import reduce

import waffle
from django.db.models import Q
from django.utils import timezone
from django.utils.safestring import mark_safe

from core.common.mongo import c_chat_context
from ct.models import UnitStatus, Response, NEED_HELP_STATUS, DONE_STATUS, NEED_REVIEW_STATUS
from ct.templatetags.ct_extras import md2html
from chat.models import Message, UnitError, YES_NO_OPTIONS
from chat.utils import is_last_thread, has_updates


class START(object):
    """
    Initialize data for viewing a courselet.

    Go immediately to first lesson (not yet completed).
    """
    title = 'Start updates flow'
    edges = (
        dict(name='next', toNode='UPDATES', title='Present common update message'),
    )

    # TODO add unittests
    def update_activity(self, chat_id: int, thread_id: int) -> None:
        c_chat_context().update_one(
            {"chat_id": chat_id},
            {"$set": {
                "thread_id": thread_id,
                f"activity.{thread_id}": timezone.now(),
                "need_faqs": False
            }},
            upsert=True
        )

    def collect_updates(self, node, fsmStack, request, **kwargs):
        # TODO add unittests
        chat = kwargs.get('chat')
        unit_lesson = kwargs.get('unitlesson')
        response = chat.message_set.filter(
            lesson_to_answer_id=unit_lesson.id,
            kind='response',
            contenttype='response',
            content_id__isnull=False).first().content
        affected_ems = [i.errorModel for i in response.studenterror_set.all()]

        context = c_chat_context().find_one({"chat_id": chat.id})
        last_access_time = context.get('activity', {}).get(f"{unit_lesson.id}") if context else None
        tz_aware_datetime = (
            last_access_time.replace(tzinfo=tz.tzutc()) if last_access_time else
            chat.last_modify_timestamp.replace(tzinfo=tz.tzutc()))

        # Collect EMs resolutions. Don't filter by user
        em_resolutions = unit_lesson.em_resolutions(tz_aware_datetime, affected_ems)
        fsmStack.state.set_data_attr('em_resolutions', em_resolutions) if em_resolutions else None

        thread_answer = unit_lesson.get_answers().first()
        interested_faqs = thread_answer.response_set.filter(
            Q(
                kind=Response.STUDENT_QUESTION, inquirycount__addedBy=request.user
            ) | Q(author=request.user, kind=Response.STUDENT_QUESTION))
        # Collect FAQ answers. Do filter by user as well as by applied previously FAQs
        faq_answers = unit_lesson.faq_answers(tz_aware_datetime, request.user, interested_faqs)
        fsmStack.state.set_data_attr('faq_answers', faq_answers) if faq_answers else None

        # Collect new EMs. Don't filter by user
        new_ems = unit_lesson.new_ems(tz_aware_datetime)
        fsmStack.state.set_data_attr('new_ems', new_ems) if new_ems else None

        # Collect ne FAQs. Do filter by user
        new_faqs = unit_lesson.new_faqs(tz_aware_datetime, request.user)
        fsmStack.state.set_data_attr('new_faqs', new_faqs) if new_faqs else None

    def start_event(self, node, fsmStack, request, **kwargs):
        """
        Event handler for START node.
        """
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Study: %s' % unit.title
        chat = kwargs.get('chat')
        unit_lesson = kwargs.get('unitlesson')
        self.collect_updates(node, fsmStack, request, **kwargs)
        self.update_activity(chat.id, unit_lesson.id)

        try:  # use unitStatus if provided
            unitStatus = fsmStack.state.get_data_attr('unitStatus')
        except AttributeError:  # create new, empty unitStatus
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)
        fsmStack.state.unitLesson = kwargs.get('unitlesson') or unitStatus.get_lesson()
        return fsmStack.state.transition(
            fsmStack, request, 'next', useCurrent=True, **kwargs
        )


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class UPDATES(object):
    """
    View a lesson updates.
    """
    get_path = get_lesson_url
    title = 'View updates'
    edges = (
        dict(name='next', toNode='FAILEDTRANSITION', title='Go to new resolutions'),
    )

    def next_edge(self, edge, *args, **kwargs):
        if args and 'em_resolutions' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_RESOLUTIONS')
        elif args and 'faq_answers' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_ANSWERS')
        elif args and 'new_ems' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_EMS')
        elif args and 'new_faqs' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_FAQS')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        data = chat.state.load_json_data()
        if any(('em_resolutions' in data,
                'faq_answers' in data,
                'new_ems' in data,
                'new_faqs' in data)):
            text = 'There are new updates for a Thread you asked for a help.'
            c_chat_context().update_one(
                {"chat_id": chat.id},
                {"$set": {"actual_ul_id": chat.state.unitLesson.id}}
            )
        else:
            text = 'I can\'t find updates for you.'
        _data = {
            'chat': chat,
            'text': text,
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_NEW_RESOLUTIONS(object):
    """
    Show all new Resolutions.
    """
    title = 'View resolutions'
    edges = (
        dict(name='next', toNode='SHOW_EM', title='Show resolution'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'New resolutions for your miscoceptions have been added. \
                     Hope it will help you to overcame your misunderstanding.',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_EM(object):
    """
    Show EM for a group of Resolutions.
    """
    title = 'Show EM'
    edges = (
        dict(name='next', toNode='SHOW_EM_RESOLUTION', title='Show resolution'),
    )

    def next_edge(self, edge, *args, **kwargs):
        if args and args[0].state.get_data_attr('resolutions_stack'):
            return edge.fromNode.fsm.get_node('SHOW_EM_RESOLUTION')
        elif args and args[0].state.get_data_attr('em_resolutions'):
            return edge.fromNode.fsm.get_node('SHOW_EM')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        em_resolutions = chat.state.get_data_attr('em_resolutions')
        if em_resolutions:
            em = em_resolutions.pop()
            chat.state.set_data_attr('resolutions_stack', em['resolutions'])
            chat.state.set_data_attr('em_resolutions', em_resolutions)
            chat.state.save_json_data()

        _data = {
            'chat': chat,
            'text': mark_safe(md2html(f'**{em.get("em_title")}** \n {em.get("em_text")}')),
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_EM_RESOLUTION(object):
    """
    Show new Resolutions one by one.
    """
    title = 'View a resolution'
    edges = (
        dict(name='next', toNode='ACT', title='Go to new answers'),
    )

    def next_edge(self, edge, *args, **kwargs):
        if args and args[0].state.get_data_attr('resolutions_stack'):
            return edge.fromNode.fsm.get_node('SHOW_EM_RESOLUTION')
        elif args and args[0].state.get_data_attr('em_resolutions'):
            return edge.fromNode.fsm.get_node('SHOW_EM')
        elif args and 'faq_answers' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_ANSWERS')
        elif args and 'new_ems' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_EMS')
        elif args and 'new_faqs' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_FAQS')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        # TODO implement Stack-like interface
        resolutions_stack = chat.state.get_data_attr('resolutions_stack')
        if resolutions_stack:
            resolution = resolutions_stack.pop()
            chat.state.set_data_attr('resolutions_stack', resolutions_stack)
            chat.state.save_json_data()

        _data = {
            'chat': chat,
            'text': mark_safe(md2html(resolution.get('text'))),
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_NEW_ANSWERS(object):
    """
    Start point in Answers presentation.
    """
    title = 'View answers'
    edges = (
        dict(name='next', toNode='SHOW_FAQ', title='Go to FAQ recall step'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        _data = {
            'chat': chat,
            'text': 'There are new answers for FAQs you are interested in',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_FAQ(object):
    """
    Show FAQ one interested in.
    """
    title = 'Recall FAQ'
    edges = (
        dict(name='next', toNode='ACT', title='Go to the next FAQ answer'),
    )

    def next_edge(self, edge, *args, **kwargs):
        chat = args[0]
        if waffle.switch_is_active('compound_faq_answer'):
            faq_answers = chat.state.get_data_attr('faq_answers')
            if faq_answers:
                faq = faq_answers.pop()
                answers = faq['answers']

                for answer in answers:
                    answer['faq_title'] = (faq.get('faq_title', ''))

                chat.state.set_data_attr('answers_stack', answers)
                chat.state.set_data_attr('faq_answers', faq_answers)
                chat.state.save_json_data()

        if args and chat.state.get_data_attr('answers_stack'):
            return edge.fromNode.fsm.get_node('SHOW_FAQ_ANSWER')
        elif args and chat.state.get_data_attr('faq_answers'):
            return edge.fromNode.fsm.get_node('SHOW_FAQ')
        elif args and 'new_ems' in chat.state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_EMS')
        elif args and 'new_faqs' in chat.state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_FAQS')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        faq_answers = chat.state.get_data_attr('faq_answers')
        if faq_answers:
            faq = faq_answers.pop()
            answers = faq['answers']

            for answer in answers:
                answer['faq_title'] = (faq.get('faq_title', ''))

            chat.state.set_data_attr('answers_stack', answers)
            chat.state.set_data_attr('faq_answers', faq_answers)
            chat.state.save_json_data()

        _data = {
            'chat': chat,
            'text': mark_safe(md2html(f'**{faq.get("faq_title")}** \n {faq.get("faq_text")}')),
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_FAQ_ANSWER(object):
    """
    Show FAQ one interested in.
    """
    title = 'Present the FAQ answers'
    edges = (
        dict(name='next', toNode='ACT', title='Go to new EMs'),
    )

    def next_edge(self, edge, *args, **kwargs):
        if args and args[0].state.get_data_attr('answers_stack'):
            return edge.fromNode.fsm.get_node('SHOW_FAQ_ANSWER')
        elif args and args[0].state.get_data_attr('faq_answers'):
            return edge.fromNode.fsm.get_node('SHOW_FAQ')
        elif args and 'new_ems' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_EMS')
        elif args and 'new_faqs' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_FAQS')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        # TODO implement Stack-like interface
        answers_stack = chat.state.get_data_attr('answers_stack')
        if answers_stack:
            answer = answers_stack.pop()
            chat.state.set_data_attr('answers_stack', answers_stack)
            chat.state.save_json_data()

        if waffle.switch_is_active('compound_faq_answer'):
            text1 = md2html(f'Below is my answer to the question you raised RE: \"{answer.get("faq_title")}\"')
            text2 = md2html(answer.get('text'))
            text = text1 + text2
        else:
            text = answer.get('text')

        _data = {
            'chat': chat,
            'text': mark_safe(text),
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class SHOW_NEW_EMS(object):
    """
    Show all new EMs.
    """
    title = 'View EMs'
    edges = (
        dict(name='next', toNode='GET_NEW_EMS', title='Go to getting Student response'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': """
                     I've added explanations for some new blindspot(s) that caused people trouble on this question.
                     Check any box(es) that seem relevant to what you were thinking. 
                    """,
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class GET_NEW_EMS(object):
    """
    Get student response for new EMs.
    """
    title = 'Get EMs from a Student'
    edges = (
        dict(name='next', toNode='ACT', title='Go to new FAQs'),
    )

    def next_edge(self, edge, *args, **kwargs):
        if args and 'new_faqs' in args[0].state.load_json_data():
            return edge.fromNode.fsm.get_node('SHOW_NEW_FAQS')
        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        unit_lesson = next_lesson
        response = chat.message_set.filter(
            lesson_to_answer_id=unit_lesson.id,
            kind='response', contenttype='response').first().content
        # TODO investigate 'content_id': uniterror.id AttributeError: 'NoneType' object has no attribute 'id'
        uniterror, _ = UnitError.objects.get_or_create(
            response=response, unit=chat.enroll_code.courseUnit.unit)
        _data = {
            'chat': chat,
            'contenttype': 'uniterror',
            'content_id': uniterror.id if uniterror else None,
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'uniterror',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    def get_errors(self, message) -> Message:
        """
        Get all error with selected ones.
        """
        checked_errors = ()
        checked_qs = UnitError.objects.filter(id=message.content_id).first()
        if checked_qs:
            checked_errors = checked_qs.response.studenterror_set.all().values_list('errorModel', flat=True)

        error_str = (
            '<li><div class="chat-check chat-selectable {}" data-selectable-attribute="errorModel" '
            'data-selectable-value="{:d}"></div><h3>{}</h3></li>'
        )
        errors = reduce(
            lambda x, y: x + y, [error_str.format(
                'chat-selectable-selected' if x.get('em_id') in checked_errors else '',
                x.get('em_id'),
                x.get('em_title')
            ) for x in message.chat.state.get_data_attr('new_ems')]
        )
        return '<ul class="chat-select-list">{}</ul>'.format(
            errors or '<li><h3>There are no misconceptions to display.</h3></li>'
        )


class SHOW_NEW_FAQS(object):
    """
    Show all new FAQs.
    """
    title = 'View FAQs'
    edges = (
        dict(name='next', toNode='FAQ_UPDATES', title='Ask for acknowlegement'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'There are new questions from Students. I hope it can help you.',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class FAQ_UPDATES(object):
    title = 'FAQ_UPDATES'
    edges = (
        dict(name='next', toNode='ACT', title='View Next Lesson'),
    )


class ACT(object):
    """
    Get acknowledgement.
    """
    title = 'Check acknowlegement'
    edges = (
        dict(name='next', toNode='GET_ACT', title='Get an acknowlegement'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'Have you anything else you are worried about?',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class GET_ACT(object):
    """
    Get acknowledgement.
    """
    title = 'Check acknowlegement'
    edges = (
        dict(name='next', toNode='TRANSITION', title='Move to the transition state'),
    )
    EVAL_TO_STATUS_MAP = {
        'yes': NEED_HELP_STATUS,
        'no': DONE_STATUS
    }

    def next_edge(self, edge, *args, **kwargs):
        if not args[0].state.parentState:
            chat = args[0]
            threads = chat.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order')
            has_updates = False

            for thread in threads:
                # TODO: move to a dedicated util
                response_msg = chat.message_set.filter(
                    lesson_to_answer_id=thread.id,
                    kind='response',
                    contenttype='response',
                    content_id__isnull=False).last()
                if not response_msg:
                    continue
                response = response_msg.content
                is_need_help = response.status in (None, NEED_HELP_STATUS, NEED_REVIEW_STATUS)
                if is_need_help and thread.updates_count(chat) > 0:
                    has_updates = True
                    break

            if not has_updates:
                return edge.fromNode.fsm.get_node('END')

        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _response_data = {
            'lesson': chat.state.unitLesson.lesson,
            'unitLesson': chat.state.unitLesson,
            'course': chat.enroll_code.courseUnit.course,
            'author': chat.user,
            'activity': chat.state.activity,
            'is_test': chat.is_test,
            'is_preview': chat.enroll_code.isPreview,
            'is_trial': chat.is_trial,
        }
        resp = Response(**_response_data)
        resp.save()

        _data = {
            'contenttype': 'response',
            'content_id': resp.id,
            'input_type': 'options',
            # This is needed to track the last response to handle status
            'lesson_to_answer_id': chat.state.unitLesson.id,
            'chat': chat,
            'owner': chat.user,
            'kind': 'response',
            'userMessage': True,
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    def get_options(self, *args, **kwargs):
        return [dict(value=i[0], text=i[1]) for i in YES_NO_OPTIONS]

    def handler(self, message, chat, request, state_handler) -> None:
        """
        Handle Student response.

        Must be used during PUT request processing.
        """
        response = message.content
        response.status = self.EVAL_TO_STATUS_MAP.get(request.data.get('option'), NEED_HELP_STATUS)
        response.save()

        message.text = dict(YES_NO_OPTIONS).get(request.data.get('option'))
        message.save()

        chat.next_point = message
        chat.last_modify_timestamp = timezone.now()
        chat.save()


class TRANSITION(object):
    title = 'Transition'
    edges = (
        dict(name='next', toNode='END', title='Get an acknowlegement'),
    )

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        """
        Edge method that moves us to right state for next lesson (or END).
        """
        fsm = edge.fromNode.fsm
        if 'next_update' in fsmStack.state.load_json_data() and \
            fsmStack.state.get_data_attr('next_update') and \
                fsmStack.state.get_data_attr('next_update').get('enabled'):
            return fsm.get_node('VIEWUPDATES')

        return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        threads = chat.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order')
        has_updates = {
            'enabled': False,
            'thread_id': None
        }

        for thread in threads:
            # TODO: move to a dedicated util
            response_msg = chat.message_set.filter(
                lesson_to_answer_id=thread.id,
                kind='response',
                contenttype='response',
                content_id__isnull=False).last()
            if not response_msg:
                continue
            response = response_msg.content
            is_need_help = response.status in (None, NEED_HELP_STATUS, NEED_REVIEW_STATUS)
            if is_need_help and thread.updates_count(chat) > 0:
                has_updates.update({'thread_id': thread.id})
                chat.state.set_data_attr('next_update', has_updates)
                chat.state.save_json_data()
                break

        if has_updates['thread_id']:
            text = f"""
                    You have completed all updates for this thread.
                    I have posted new messages to help you in the thread "{thread.lesson.title}".
                    Would you like to view these updates now?
                    """
        elif chat.state.parentState:
            next_lesson = None
            parent = chat.state.parentState
            while parent and not parent.fsmNode.fsm.fsm_name_is_one_of('chat'):
                parent = parent.parentState
            if parent:
                status = parent.get_data_attr('unitStatus')
                next_lesson = status.get_next_lesson().lesson.title if status.get_next_lesson() else None
            text = f"""
                    You have completed all updates for this thread.
                    Click on Continue below to view your next thread "{next_lesson}".
                    """ if next_lesson else 'You have completed this thread.'
        else:
            text = 'You have completed all updates for this thread.'

        _data = {
            'chat': chat,
            'text': text,
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'sub_kind': 'transition',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message

    def get_options(self, *args, **kwargs) -> list:
        """
        We should not reach this code on last transition node w/o updates.
        """
        state = args[0].state
        parent = state.parentState

        while parent and not parent.fsmNode.fsm.fsm_name_is_one_of('chat'):
            parent = parent.parentState

        options = [{'value': 'next_thread', 'text': 'Continue'}] \
            if parent and not is_last_thread(parent) else []

        if has_updates(state):
            options.insert(0, {'value': 'next_update', 'text': 'Yes'})
            if len(options) == 2:
                options[1]['text'] = 'No'

        return options

    def handler(self, message, chat, request, state_handler) -> None:
        """
        Handle Student transition decision.

        Must be used during PUT request processing.
        """
        data = request.data.get('option')
        if data == 'next_update':
            data = chat.state.get_data_attr('next_update')
            data.update({'enabled': True})
            chat.state.set_data_attr('next_update', data)
            chat.state.save_json_data()
        chat.next_point = state_handler.next_point(
            current=message.content,
            chat=chat,
            message=message,
            request=request)
        chat.save()


class VIEWUPDATES(object):
    title = 'END'
    edges = (
        dict(name='next', toNode='END', title='Get updates'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'Hey hey UPD',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class FAILEDTRANSITION(object):
    """
    There we want to ask a Student to submit the transition to the next Thread.
    """
    title = 'Transition'
    edges = (
        dict(name='next', toNode='END', title='Move to the END'),
    )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'Look\'s like you revieved updates in a different way.',
            'owner': chat.user,
            'input_type': 'options',
            'kind': 'button',
            'sub_kind': 'transition',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


class END(object):
    """
    Final None.

    Intend is to me a marker for a FSM handler to remove a state.
    """
    title = 'Courselet core lessons completed'

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        _data = {
            'chat': chat,
            'text': 'Let\'s return to your previous state.',
            'owner': chat.user,
            'input_type': 'custom',
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()
        return message


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='updates',
        hideTabs=True,
        title='Present updates for a particular Thread.',
        pluginNodes=[
            START,
            UPDATES,
            SHOW_NEW_RESOLUTIONS,
            SHOW_EM,
            SHOW_EM_RESOLUTION,
            SHOW_NEW_ANSWERS,
            SHOW_FAQ,
            SHOW_FAQ_ANSWER,
            SHOW_NEW_EMS,
            GET_NEW_EMS,
            SHOW_NEW_FAQS,
            FAQ_UPDATES,
            ACT,
            GET_ACT,
            TRANSITION,
            VIEWUPDATES,
            FAILEDTRANSITION,
            END
        ],

    )
    return (spec,)
