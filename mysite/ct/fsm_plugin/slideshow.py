from ct.models import UnitLesson


def next_lesson(self, edge, fsmStack, request, unit=None, **kwargs):
    """
    Edge method that moves us to right state for next lesson (or END).
    """
    fsm = edge.fromNode.fsm
    if unit:  # get first lesson
        fsmStack.state.unitLesson = unit.get_exercises()[0]
    else:
        ul = fsmStack.state.unitLesson
        answers = ul.get_answers()
        if ul.is_question() and len(answers) > 0:  # get the answer
            fsmStack.state.unitLesson = answers[0]
        else:
            if ul.parent:  # if ul is answer, use its linked question
                ul = ul.parent
            try:
                fsmStack.state.unitLesson = ul.get_next_lesson()
            except UnitLesson.DoesNotExist:
                return fsm.get_node('END')
    return edge.toNode  # just show it as a LESSON slide


QuitEdgeData = dict(
    name='quit', toNode='END', title='End this slideshow', showOption=True,
    description="If you don't want to view any more slides, exit the slideshow",
    help='''Click here to end this slideshow. '''
)


ContentsEdgeData = dict(
    name='contents', toNode='CHOOSE', showOption=True,
    title='View Table of Contents',
    description='overview of all slides in the slideshow',
    help='Click here to view the Table of Contents'
)


class START(object):
    """
    Initialize data for viewing a courselet, and go immediately
    to first lesson.
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        'event handler for START node'
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Slideshow: %s' % unit.title
        return fsmStack.state.transition(fsmStack, request, 'next',
                                         unit=unit, **kwargs)
    next_edge = next_lesson
    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Lesson'),
        )


class LESSON(object):
    """
    View a lesson explanation.
    """
    next_edge = next_lesson
    # node specification data goes here
    path = 'ct:lesson_read'
    title = 'View an explanation or question'
    help = '''After viewing this slide, click Next to move to the next slide,
    or click the Slideshow menu above for more options such as discussion
    of this slide, Table of Contents, etc.'''
    edges = (
            dict(name='next', toNode='LESSON', title='View Next Slide',
                 showOption=True),
            dict(name='faq', toNode='FAQ', showOption=True,
                 title='Discussion of this slide',
                 description='Comment on or view discussion of this slide',
                 help='Click here to join the discussion'),
            ContentsEdgeData,
            QuitEdgeData,
        )


class FAQ(object):
    """
    Discussion of this slide.
    """
    create_Comment_edge = next_lesson
    # node specification data goes here
    path = 'ct:ul_faq_student'
    title = 'Comment on or view discussion of the last slide you viewed'
    help = '''You can click on discussion threads on this page, if any,
    or write a new comment / question about this slide.  Or you can click
    the Slideshow menu above for more options.'''
    edges = (
            dict(name='create_Comment', toNode='LESSON',
                 title='Go to Next Slide', showOption=True),
            dict(name='slide', toNode='LESSON', showOption=True,
                 title='Return to this slide',
                 description='Go back to the last slide you viewed'),
            ContentsEdgeData,
            QuitEdgeData,
        )


class CHOOSE(object):
    """
    Overview list of slides, for you to jump to any slide in the slideshow.
    """
    # node specification data goes here
    path = 'ct:unit_lessons_student'
    title = 'Slideshow Table of Contents'
    help = '''View the table of contents below,
    choose a slide you want to view,
    then click its Jump to this slide button.
    Alternatively, click the Slideshow menu item above for more options,
    such as returning to your current slide.'''
    edges = (
            dict(name='select_UnitLesson', toNode='LESSON',
                 title='Jump to this slide',
                 help='''Click here to jump to this slide.'''),
            dict(name='resume', toNode='LESSON', showOption=True,
                 title='Resume slideshow at the current slide',
                 description='return to the last slide you viewed',
                 help='''Click here to resume the slideshow.'''),
            QuitEdgeData,
        )


class END(object):
    # node specification data goes here
    path = 'ct:unit_concepts_student'
    title = 'Courselet slide show completed'
    help = '''Thanks for viewing this slide show.
    See below for suggested next steps on concepts you can study in
    this courselet.'''


def get_specs():
    'get FSM specifications stored in this file'
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='slideshow',
        hideTabs=True,
        title='View courselet as a slide show',
        pluginNodes=[START, LESSON, FAQ, CHOOSE, END],
    )
    return (spec,)
