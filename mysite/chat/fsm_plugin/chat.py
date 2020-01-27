from django.utils import timezone

from core.common.mongo import c_chat_context
from ct.models import UnitStatus, UnitLesson, Lesson, STATUS_CHOICES
from chat.models import Message, ChatDivider


def next_lesson_after_errors(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    if c_chat_context().find_one({"chat_id": fsmStack.id}).get('need_faqs'):
        return fsm.get_node('FAQ')

    return edge.toNode


def next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    unitStatus = fsmStack.state.get_data_attr('unitStatus')
    if useCurrent:
        nextUL = unitStatus.get_lesson()
        return edge.toNode
    else:
        nextUL = unitStatus.start_next_lesson()
    if not nextUL:
        unit = fsmStack.state.get_data_attr('unit')
        if unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT, order__isnull=True
        ).exists():
            return fsm.get_node('IF_RESOURCES')
        else:
            return fsm.get_node('END')
    else:  # just a lesson to read
        fsmStack.state.unitLesson = nextUL

        return edge.toNode


def next_lesson_after_title(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    unitStatus = fsmStack.state.get_data_attr('unitStatus')
    nextUL = unitStatus.get_lesson()
    answer = nextUL.get_answers().first()
    # Update chat context
    # Don't ask
    chat = fsmStack
    c_chat_context().update_one(
        {"chat_id": chat.id},
        {"$set": {
            "actual_ul_id": answer.id if answer else nextUL.id,
            "thread_id": nextUL.id,
            f"activity.{nextUL.id}": timezone.now(),
            "need_faqs": False
        }},
        upsert=True
    )
    if nextUL.is_question():
        return fsm.get_node(name='ASK')
    else:  # just a lesson to read
        return edge.toNode


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if fsmStack.state.unitLesson.lesson.enable_auto_grading and not fsmStack.state.fsmNode.name == 'GRADING':
        return fsm.get_node('GRADING')

    if fsmStack.next_point.content.selfeval != 'correct':
        if (fsmStack.next_point.content.unitLesson.get_errors() or
                fsmStack.next_point.content.lesson.add_unit_aborts and
                fsmStack.next_point.content.unitLesson.unit.get_aborts()):
            c_chat_context().update_one(
                {"chat_id": fsmStack.id},
                {"$set": {"need_faqs": True}},
                upsert=True
            )
            return fsm.get_node('ERRORS')
        else:
            resp = fsmStack.next_point.content
            resp.status = 'help'
            resp.save()
            return fsm.get_node('FAQ')

    return edge.toNode


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


class START(object):
    """
    Initialize data for viewing a courselet, and go immediately
    to first lesson (not yet completed).
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        """
        Event handler for START node.
        """
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Study: %s' % unit.title

        try:  # use unitStatus if provided
            unitStatus = fsmStack.state.get_data_attr('unitStatus')
        except AttributeError:  # create new, empty unitStatus
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)
        fsmStack.state.unitLesson = unitStatus.get_lesson()
        return fsmStack.state.transition(
            fsmStack, request, 'next', useCurrent=True, **kwargs
        )

    next_edge = next_lesson
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
        dict(name='next', toNode='TITLE', title='View Next Lesson'),
    )


class TITLE(object):
    """
    View a lesson explanation.
    """
    next_edge = next_lesson_after_title
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='LESSON', title='View Next Lesson'),
    )

    def _update_thread_id(self, chat, thread_id):
        c_chat_context().update_one(
            {"chat_id": chat.id},
            {"$set": {
                "thread_id": thread_id,
            }},
            upsert=True
        )

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs):
        self._update_thread_id(chat, next_lesson.id)

        divider = ChatDivider(text=next_lesson.lesson.title, unitlesson=next_lesson)
        divider.save()

        _data = {
            'contenttype': 'chatdivider',
            'chat': chat,
            'content_id': divider.id,
            'input_type': 'custom',
            'type': 'breakpoint',
            'chat': chat,
            'owner': chat.user,
            'kind': 'message',
            'is_additional': is_additional
        }
        message = Message(**_data)
        message.save()

        return message


class LESSON(object):
    """
    View a lesson explanation.
    """
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='TRANSITION', title='View Next Lesson'),
    )


class ASK(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='GET_ANSWER', title='Answer a question'),
    )


class GET_ANSWER(object):
    """
    Get answer and decide where to go next.
    """
    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm

        unitStatus = fsmStack.state.get_data_attr('unitStatus')
        unit_lesson = unitStatus.get_lesson()
        if unit_lesson.sub_kind == Lesson.MULTIPLE_CHOICES and unit_lesson.lesson.mc_simplified:
            return fsm.get_node('TRANSITION')
        else:
            return edge.toNode

    title = 'It is time to answer'
    edges = (
        dict(name='next', toNode='CONFIDENCE', title='Go to confidence'),
    )


class CONFIDENCE(object):
    title = 'How confident are you?'
    edges = (
        dict(name='next', toNode='GET_CONFIDENCE', title='Go to choosing your confidence'),
    )


class GET_CONFIDENCE(object):
    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        """
        Options:
            1. Correct choice -> next Lesson
            2. Incorrect choice -> ERRORS
            3. Partially correct choice -> ERRORS
        """
        fsm = edge.fromNode.fsm

        if not fsmStack.next_point.content.selfeval:
            return edge.toNode

        if fsmStack.next_point.content.selfeval != 'correct':
            return fsm.get_node('INCORRECT_ANSWER')
        elif fsmStack.next_point.content.selfeval == 'correct':
            return fsm.get_node('CORRECT_ANSWER')
        else:
            return edge.toNode

        return edge.toNode

    title = 'Choose confidence'
    edges = (
        dict(name='next', toNode='ASSESS', title='Go to self-assessment'),
    )


class CORRECT_ANSWER(object):
    title = 'Show correct answer for Multiple Choices'
    edges = (
        dict(name='next', toNode='TRANSITION', title='Assess yourself'),
    )


class INCORRECT_ANSWER(object):
    title = 'Show correct answer for Multiple Choices'
    edges = (
        dict(name='next', toNode='INCORRECT_CHOICE', title='Assess yourself'),
    )


class INCORRECT_CHOICE(object):
    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        if (fsmStack.next_point.content.unitLesson.get_errors() or
                fsmStack.next_point.content.lesson.add_unit_aborts and
                fsmStack.next_point.content.unitLesson.unit.get_aborts()):
            c_chat_context().update_one(
                {"chat_id": fsmStack.id},
                {"$set": {"need_faqs": True}},
                upsert=True
            )
            return fsm.get_node('ERRORS')
        else:
            return fsm.get_node('FAQ')

    title = 'Show incorrect choice for Multiple Choices'
    edges = (
        dict(name='next', toNode='TRANSITION', title='Assess yourself'),
    )


class ASSESS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='ASSESS_QUESTION_MESSAGE', title='Assess yourself'),
    )


class ASSESS_QUESTION_MESSAGE(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='GET_ASSESS', title='Assess yourself'),
    )
    help = 'How close was your answer to the one shown here?'


class GET_ASSESS(object):
    get_path = get_lesson_url
    next_edge = check_selfassess_and_next_lesson
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='TRANSITION', title='View Next Lesson'),
    )


class GRADING(object):
    get_path = get_lesson_url
    next_edge = check_selfassess_and_next_lesson
    # node specification data goes here
    title = 'Grading for student answer'
    edges = (
        dict(name='next', toNode='TRANSITION', title='View Next Lesson'),
    )


class ERRORS(object):
    get_path = get_lesson_url
    # node specification data goes here
    title = 'Error options'
    edges = (
        dict(name='next', toNode='GET_ERRORS', title='Choose errors'),
    )


class GET_ERRORS(object):
    get_path = get_lesson_url
    next_edge = next_lesson_after_errors
    # node specification data goes here
    title = 'Classify your error(s)'
    edges = (
        dict(name='next', toNode='TRANSITION', title='View Next Lesson'),
    )


class IF_RESOURCES(object):
    help = '''Congratulations! You have completed the core lessons for this
              courselet.'''

    title = 'Courselet core lessons completed'
    edges = (
        dict(name='next', toNode='END', title='View Next Lesson'),
    )


class FAQ(object):
    title = 'FAQ'
    edges = (
        dict(name='next', toNode='TRANSITION', title='View Next Lesson'),
    )


class TRANSITION(object):
    title = 'Transition'
    edges = (
        dict(name='next', toNode='TITLE', title='Get an acknowlegement'),
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

        unitStatus = fsmStack.state.get_data_attr('unitStatus')
        currentLesson = unitStatus.get_lesson()

        if useCurrent:
            nextUL = currentLesson
            return edge.toNode
        else:
            nextUL = unitStatus.start_next_lesson()
        if not nextUL:
            unit = fsmStack.state.get_data_attr('unit')
            if unit.unitlesson_set.filter(
                kind=UnitLesson.COMPONENT, order__isnull=True
            ).exists():
                return fsm.get_node('IF_RESOURCES')
            else:
                return fsm.get_node('END')
        else:  # just a lesson to read
            fsmStack.state.unitLesson = nextUL

            return edge.toNode

    def get_message(self, chat, next_lesson, is_additional, *args, **kwargs) -> Message:
        threads = chat.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order')
        has_updates = {
            'enabled': False,
            'thread_id': None
        }
        for thread in threads:
            if thread.updates_count(chat) > 0:
                has_updates.update({'thread_id': thread.id})
                chat.state.set_data_attr('next_update', has_updates)
                chat.state.save_json_data()
                break
        if has_updates['thread_id']:
            text = f"""
                    You have completed this thread.
                    I have posted new messages to help you in the thread "{thread.lesson.title}".
                    Would you like to view these updates now?
                    """
        else:
            text = 'Now you can move to the next lesson'
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
        options = [{'value': 'next_thread', 'text': 'View next thread'}]
        state = args[0].state
        if state and \
            'next_update' in state.load_json_data() and \
                state.get_data_attr('next_update') and \
                state.get_data_attr('next_update').get('thread_id'):
            options.insert(0, {'value': 'next_update', 'text': 'View updates'})
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
    title = 'VIEWUPDATES'
    edges = (
        dict(name='next', toNode='TITLE', title='Get updates'),
    )

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        """
        Edge method that moves us to right state for next lesson (or END).
        """
        fsm = edge.fromNode.fsm
        unitStatus = fsmStack.state.get_data_attr('unitStatus')
        currentLesson = unitStatus.get_lesson()

        if useCurrent:
            nextUL = currentLesson
            return edge.toNode
        else:
            nextUL = unitStatus.start_next_lesson()
        if not nextUL:
            unit = fsmStack.state.get_data_attr('unit')
            if unit.unitlesson_set.filter(
                kind=UnitLesson.COMPONENT, order__isnull=True
            ).exists():
                return fsm.get_node('IF_RESOURCES')
            else:
                return fsm.get_node('END')
        else:  # just a lesson to read
            fsmStack.state.unitLesson = nextUL

            return edge.toNode


class END(object):
    # node specification data goes here
    def get_help(self, node, state, request):
        'provide help messages for all views relevant to this stage.'
        unit = state.get_data_attr('unit')
        lessons = list(
            unit.unitlesson_set.filter(
                kind=UnitLesson.COMPONENT, order__isnull=True
            )
        )
        if lessons:
            return '''Please look over the available resources in the side panel.'''
        else:
            return '''Congratulations! You have completed the core lessons for this
                      courselet.'''
    title = 'Courselet core lessons completed'


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='chat',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[
            START,
            TITLE,
            LESSON,
            ASK,
            GET_ANSWER,
            CONFIDENCE,
            GET_CONFIDENCE,
            CORRECT_ANSWER,
            INCORRECT_ANSWER,
            INCORRECT_CHOICE,
            ASSESS,
            ASSESS_QUESTION_MESSAGE,
            GET_ASSESS,
            GRADING,
            ERRORS,
            GET_ERRORS,
            IF_RESOURCES,
            FAQ,
            TRANSITION,
            VIEWUPDATES,
            END
        ],

    )
    return (spec,)
