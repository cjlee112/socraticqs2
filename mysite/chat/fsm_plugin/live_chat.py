from core.common.mongo import c_chat_context
from chat.models import Message, ChatDivider


def ask_edge(self, edge, fsmStack, request, **kwargs):
    """
    Try to transition to ASK, or WAIT_ASK if not ready.
    """
    fsm = edge.fromNode.fsm
    if not fsmStack.state.linkState:  # instructor detached
        return fsm.get_node('END')
    elif fsmStack.state.linkState.fsmNode.node_name_is_one_of('QUESTION'):  # in progress
        fsmStack.state.unitLesson = fsmStack.state.linkState.unitLesson
        fsmStack.state.save()
        return edge.toNode  # so go straight to asking question
    return fsm.get_node('WAIT_ASK')


def assess_edge(self, edge, fsmStack, request, **kwargs):
    """
    Try to transition to ASSESS, or WAIT_ASSESS if not ready,
    or jump to ASK if a new question is being asked.
    """
    fsm = edge.fromNode.fsm
    if not fsmStack.state.linkState:  # instructor detached
        return fsm.get_node('END')
    elif fsmStack.state.linkState.fsmNode.node_name_is_one_of('QUESTION'):
        if fsmStack.state.unitLesson == fsmStack.state.linkState.unitLesson:
            return fsm.get_node('WAIT_ASSESS')
        else:  # jump to the new question
            fsmStack.state.unitLesson = fsmStack.state.linkState.unitLesson
            fsmStack.state.save()
            return fsm.get_node('TITLE')
    else:  # pragma: no cover
        if not fsmStack.next_point.response_to_check.selfeval:
            return edge.toNode
        if fsmStack.next_point.response_to_check.selfeval != 'correct':
            return fsm.get_node('INCORRECT_ANSWER')
        elif fsmStack.next_point.response_to_check.selfeval == 'correct':
            return fsm.get_node('CORRECT_ANSWER')
        return edge.toNode  # go to assessment


def get_lesson_url(self, node, state, request, **kwargs):
    """
    Get URL for any lesson.
    """
    course = state.get_data_attr('course')
    unitStatus = state.get_data_attr('unitStatus')
    ul = unitStatus.get_lesson()
    return ul.get_study_url(course.pk)


def check_selfassess_and_next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs):
    fsm = edge.fromNode.fsm

    if fsmStack.state.unitLesson.lesson.enable_auto_grading and not fsmStack.state.fsmNode.name == 'GRADING':
        return fsm.get_node('GRADING')

    # TODO add tests for this case
    if fsmStack.next_point.content.selfeval != 'correct':  # pragma: no cover
        if (fsmStack.next_point.content.unitLesson.get_errors() or
            fsmStack.next_point.content.lesson.add_unit_aborts and
            fsmStack.next_point.content.unitLesson.unit.get_aborts()):
            return fsm.get_node('ERRORS')
        else:
            resp = fsmStack.next_point.content
            resp.status = 'help'
            resp.save()

    return fsm.get_node('WAIT_ASK')
    # return next_lesson(self, edge, fsmStack, request, useCurrent=False, **kwargs)


def next_incorrect_choice_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        if (fsmStack.next_point.response_to_check.unitLesson.get_errors() or
            fsmStack.next_point.response_to_check.lesson.add_unit_aborts and
            fsmStack.next_point.response_to_check.unitLesson.unit.get_aborts()):
            return fsm.get_node('ERRORS')
        else:
            return edge.toNode


def next_edge_teacher_coherent(nodes, fail_node='WAIT_ASK'):
    def wrapp(func):
        def wrapper(self, edge, fsmStack, request, **kwargs):
            if not fsmStack.state or fsmStack.state and not fsmStack.state.linkState:
                return edge.fromNode.fsm.get_node('END')
            if not fsmStack.state.linkState.fsmNode.node_name_is_one_of(*nodes):
                # print "-------> Student in node {} and \n TEACHER in node {}, allowed nodes for teacher {}".format(
                #     fsmStack.state.fsmNode.name,
                #     fsmStack.state.linkState.fsmNode.name,
                #     nodes
                #     )
                return edge.fromNode.fsm.get_node('WAIT_ASK')
            return func(self, edge, fsmStack, request,  **kwargs)
        return wrapper
    return wrapp


class INCORRECT_ANSWER(object):  # pragma: no cover
    title = 'Show correct answer for Multiple Choices'
    edges = (
            dict(name='next', toNode='INCORRECT_CHOICE', title='Assess yourself'),
        )


class INCORRECT_CHOICE(object):  # pragma: no cover
    title = 'Show incorrect choice for Multiple Choices'
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCYLE"])(next_incorrect_choice_edge)

    edges = (
        dict(name='next', toNode='WAIT_ASK', title='Assess yourself'),
    )


class CORRECT_ANSWER(object):  # pragma: no cover
    title = 'Show correct answer for Multiple Choices'
    edges = (
        dict(name='next', toNode='WAIT_ASK', title='Assess yourself'),
    )
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCLE"])(
        lambda self, edge, *args, **kwargs: edge.toNode
    )


class START(object):
    """
    In this activity you will answer questions
    presented by your instructor in-class.
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        'event handler for START node'
        fsmStack.state.activity = fsmStack.state.linkState.activity
        unit = fsmStack.state.linkState.get_data_attr('unit')
        course = fsmStack.state.linkState.get_data_attr('course')
        fsmStack.state.set_data_attr('unit', unit)
        fsmStack.state.set_data_attr('course', course)
        fsmStack.state.title = 'Live: %s' % unit.title
        return node.get_path(fsmStack.state, request, **kwargs)
    next_edge = ask_edge
    # node specification data goes here
    path = 'fsm:fsm_node'
    title = 'Now Joining a Live Classroom Session'
    edges = (
        dict(name='next', toNode='WAIT_ASK', title='Start answering questions'),
    )


class WAIT_ASK(object):
    """
    The instructor has not assigned the next exercise yet.
    Please wait, and click the Next button when the instructor tells
    you to do so, or when the live classroom session is over.
    """
    next_edge = ask_edge
    # node specification data goes here
    path = 'fsm:fsm_node'
    title = 'Wait for the Instructor to Assign a Question'
    edges = (
        dict(name='next', toNode='TITLE', title='See if question assigned'),
    )


class TITLE(object):
    """
    View a lesson explanation.
    """
    # get_path = get_lesson_url
    # node specification data goes here
    title = 'View an explanation'
    edges = (
        dict(name='next', toNode='ASK', title='View Next Lesson'),
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


class ASK(object):
    """
    In this stage you write a brief answer to a conceptual question.
    """
    @next_edge_teacher_coherent(["QUESTION"])
    def next_edge(self, edge, fsmStack, request, response=None, **kwargs):
        if response:
            fsmStack.state.set_data_attr('response', response)
            fsmStack.state.save_json_data()
        return ask_edge(
            self, edge, fsmStack, request, response=response, **kwargs
        )
    # node specification data goes here

    # def next_edge(self, edge, fsmStack, request, response=None, **kwargs):
    #     return edge.toNode
    # next_edge = ask_edge
    path = 'ct:ul_respond'
    title = 'Answer this Question'
    help = """Listen to your instructor's explanation of this question,
    and ask about anything that's unclear about what you're being asked.
    When the instructor tells you to start, think about the question
    for a minute or two, then briefly write whatever answer you
    come up with. """
    edges = (
        dict(name='next', toNode='GET_ANSWER', title='Answer a question'),
    )


class GET_ANSWER(object):
    get_path = get_lesson_url
    # node specification data goes here
    next_edge = next_edge_teacher_coherent(["QUESTION", "ANSWER"])(
        lambda self, edge, *args, **kwargs: edge.toNode
    )
    title = 'It is time to answer'
    edges = (
        dict(name='next', toNode='CONFIDENCE', title='Go to self-assessment'),
    )


class CONFIDENCE(object):
    title = 'How confident are you?'
    edges = (
        dict(name='next', toNode='GET_CONFIDENCE', title='Go to choosing your confidence'),
    )


class GET_CONFIDENCE(object):
    title = 'Choose confidence'
    edges = (
        dict(name='next', toNode='WAIT_ASSESS', title='Go to self-assessment'),
    )


class WAIT_ASSESS(object):
    """
    The instructor has not ended the question period yet.
    Please wait, and click the Next button when the instructor tells
    you to do so, or when the live classroom session is over.
    """
    # next_edge = assess_edge
    # node specification data goes here
    path = 'fsm:fsm_node'
    title = 'Wait for the Instructor to End the Question'
    edges = (
        dict(name='next', toNode='ASSESS', title='See if question done'),
    )

    @next_edge_teacher_coherent(["QUESTION", "ANSWER", "RECYCLE"])
    def next_edge(self, edge, fsmStack, request, response=None, **kwargs):
        if response:
            fsmStack.state.set_data_attr('response', response)
            fsmStack.state.save_json_data()
        return assess_edge(self, edge, fsmStack, request, response=response,
                           **kwargs)


class ASSESS(object):
    """
    In this stage you assess your own answer vs. the correct answer.
    """
    next_edge = next_edge_teacher_coherent(["QUESTION", "ANSWER", "RECYCLE"])(assess_edge)
    # node specification data goes here
    path = 'ct:assess'
    title = 'Assess your answer'
    help = """Listen to your instructor's explanation of the answer,
    then categorize your assessment, and how well you feel you
    understand this concept now. """

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
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCYLE"])(check_selfassess_and_next_lesson)
    # node specification data goes here
    title = 'Assess your answer'
    edges = (
        dict(name='next', toNode='WAIT_ASK', title='View Next Lesson'),
    )


class GRADING(object):
    get_path = get_lesson_url
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCYLE"])(check_selfassess_and_next_lesson)
    # node specification data goes here
    title = 'Grading for student answer'
    edges = (
        dict(name='next', toNode='WAIT_ASK', title='View Next Lesson'),
    )


class ERRORS(object):
    """
    In this stage you assess whether you made any of the common errors for this concept.
    """
    # next_edge = ask_edge
    # node specification data goes here
    title = 'Error options'
    edges = (
        dict(name='next', toNode='GET_ERRORS', title='Choose errors'),
    )
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCLE"])(
        lambda self, edge, *args, **kwargs: edge.toNode
    )


class GET_ERRORS(object):
    get_path = get_lesson_url
    # next_edge = next_lesson
    # node specification data goes here
    title = 'Classify your error(s)'
    edges = (
        dict(name='next', toNode='WAIT_ASK', title='View next question'),
    )
    next_edge = next_edge_teacher_coherent(["ANSWER", "RECYCLE"])(
        lambda self, edge, *args, **kwargs: edge.toNode
    )


class END(object):
    # node specification data goes here
    path = 'ct:unit_tasks_student'
    title = 'Live classroom session completed'
    help = '''The instructor has ended the Live classroom session.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='live_chat',
        hideTabs=True,
        title='Join a Live Classroom Session',
        pluginNodes=[
            START,
            WAIT_ASK,
            TITLE,
            ASK,
            GET_ANSWER,
            CONFIDENCE,
            GET_CONFIDENCE,
            CORRECT_ANSWER,
            INCORRECT_ANSWER,
            INCORRECT_CHOICE,
            WAIT_ASSESS,
            ASSESS,
            ASSESS_QUESTION_MESSAGE,
            GET_ASSESS,
            GRADING,
            ERRORS,
            GET_ERRORS,
            END
        ],
    )
    return (spec,)
