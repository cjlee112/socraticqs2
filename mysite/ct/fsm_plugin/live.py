from fsm.models import ActivityLog


def quit_edge(self, edge, fsmStack, request, **kwargs):
    """
    Edge method that terminates this live-session.
    """
    for studentState in fsmStack.state.linkChildren.all():
        studentState.linkState = None  # detach from our state
        studentState.save()
    return edge.toNode


QuitEdgeData = dict(
    name='quit', toNode='END', title='End this live-session',
    description='''If you have no more questions to ask, end
    this live session.''',
    help='''Click here to end this live-session. ''',
    showOption=True,
)


class START(object):
    """
    This activity will allow you to select questions
    for students to answer in-class.
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        'event handler for START node'
        unit = fsmStack.state.get_data_attr('unit')
        course = fsmStack.state.get_data_attr('course')
        fsmStack.state.title = 'Teaching: %s' % unit.title
        activity = ActivityLog(
            fsmName=fsmStack.state.fsmNode.fsm.name,
            course=course
        )  # create a new activity
        activity.save()
        fsmStack.state.activity = activity
        fsmStack.state.isLiveSession = True
        return node.get_path(fsmStack.state, request, **kwargs)
    # node specification data goes here
    path = 'fsm:fsm_node'
    title = 'Start Teaching a Live Session'
    edges = (
            dict(name='next', toNode='CHOOSE', title='Start asking a question',
                 showOption=True),
        )


class CHOOSE(object):
    """
    At this step you choose a question to ask in this live session.
    """
    def select_UnitLesson_filter(self, edge, unit_lesson):
        """
        Return True if input is acceptable for this edge.
        input: UnitLesson
        """
        return unit_lesson.is_question()

    # node specification data goes here
    path = 'ct:unit_lessons'
    title = 'Choose a Question to Ask'
    help = '''Select a question below that you want to ask your students in this
    live session, then click its Ask this Question button. '''
    edges = (
            dict(name='select_UnitLesson', toNode='QUESTION',
                 title='Ask this question',
                 help='''Click here to start posing this question to your
                 live session students.'''),
        )


class QUESTION(object):
    path = 'ct:live_question'
    title = 'Ask a question to students in a classroom live-session'
    help = '''Explain the question and ask if there are any aspects
    where the students are unsure what exactly they are being asked.
    Then click the START button and ask the students to think about
    the question for a minute or so, then briefly type whatever
    answer they come up with.  You will be able to monitor their
    progress on this page in real-time.'''
    edges = (
        dict(name='next', toNode='ANSWER', title='Present the answer',
             help='''Click here to move to the assessment stage of this
             exercise. '''),
    )


class ANSWER(object):
    quit_edge = quit_edge
    path = 'ct:ul_teach'
    title = 'Present the answer for students to self-assess'
    help = '''Explain the answer and ask if there are any aspects
    the students are wondering about. Then ask them to assess
    their own answer against the correct answer'''
    edges = (
        dict(name='next', toNode='RECYCLE', title='Finish this question',
             help='''Click here to end this question. '''),
        QuitEdgeData,
    )


class RECYCLE(object):
    """
    You have completed presenting this question.  Do you want to
    ask the students another question, or end this live session?
    """
    def next_edge(self, edge, fsmStack, request, pageData=None, **kwargs):
        'make sure timer is reset before going to another question'
        pageData.set_refresh_timer(request, False)
        return edge.toNode
    path = 'fsm:fsm_node'
    title = 'Do you want to ask another question?'
    edges = (
        dict(name='next', toNode='CHOOSE', title='Move on to another question',
             help='''Click here to choose another question to ask. '''),
        QuitEdgeData,
    )


class END(object):
    # node specification data goes here
    path = 'ct:unit_tasks'
    title = 'Live Session completed'
    help = '''You have successfully ended this live-session.
    See below for suggested next steps for what you can work on next
    to help students with this courselet.'''


def get_specs():
    'get FSM specifications stored in this file'
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='liveteach',
        title='Teach a live (classroom) session',
        description='''You can begin teaching this courselet in a
                    live classroom session by clicking here:''',
        pluginNodes=[START, CHOOSE, QUESTION, ANSWER, RECYCLE, END],
        fsmGroups=('teach/unit/published',),
    )
    return (spec,)
