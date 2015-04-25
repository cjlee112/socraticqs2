from ct.models import *

class START(object):
    '''Typically this involves several steps:
    search Courselets for an existing lesson that matches your goals;
    if not, define the concept your new lesson will be about;
    write a new lesson.'''
    # node specification data goes here
    path = 'ct:fsm_node'
    title = 'How to Add a Lesson to a Courselet'
    edges = (
            dict(name='next', toNode='SEARCH', title='Search Lessons'),
        )

class SEARCH(object):
    '''In this stage, you search Courselets to see if you can find
    an existing Lesson that you can use as-is or with your own edits.'''
    path = 'ct:unit_lessons'
    title = 'Search for suitable Lessons'
    help = '''Enter a search term below to search Courselets for lessons,
    then click on Lesson titles to see match your teaching goal.
    If you find nothing suitable, click the Add a New Lesson button
    on the Navigation bar above, then click Choose a Concept.'''
    edges = (
            dict(name='next', toNode='CONCEPTS', title='Choose a Concept',
                 description='''If you want to write a new Lesson, click here
                 to choose what concept your new lesson will be about''',
                 showOption=True),
            dict(name='create_UnitLesson', toNode='END', title='Added a lesson'),
        )

class CONCEPTS(object):
    '''In this stage, you identify the main concept that you want to
    teach about in your new Lesson. '''
    def get_help(self, node, state, request):
        'provide help messages for all views relevant to this stage.'
        hits = {'ct:wikipedia_concept':
            '''If this definition approximately matches the concept you
            want to teach about, click Add.  Otherwise click the browser
            Back button to go back to the Search concepts page.''',
            
            'ct:concept_teach':
            '''If this definition approximately matches the concept you
            want to teach about, click Add.  Otherwise click the browser
            Back button to go back to the Search concepts page.''',

            'ct:concept_lessons':
            '''If this definition approximately matches the concept you
            want to teach about, you can write a new Lesson about it
            below.'''
        }
        if state.fsm_on_path(request.path):
            return node.help
        if request.path.startswith(state.path):
            return hits.get(request.resolver_match.view_name, None)
    path = 'ct:unit_concepts'
    title = 'What concept do you want to teach about?'
    help = '''The first step of writing a new Lesson, is to choose what concept
    you want it to teach about.  You can either click one of the concepts
    listed below, or enter a search term to search for the most relevant
    concept, then click on a concept to see if it matches your main aim.
    If searching finds nothing suitable, you can write a brief definition
    of the concept you want to teach below.'''
    edges = (
            dict(name='add_Concept', toNode='WRITE', title='write your lesson'),
            dict(name='create_Concept', toNode='WRITE', title='write your lesson'),
            dict(name='create_UnitLesson', toNode='END', title='Added a lesson'),
        )

class WRITE(object):
    '''In this stage, you write a new Lesson about the concept you chose. '''
    path = 'ct:concept_lessons'
    title = 'Write a new Lesson about this concept'
    help = '''Please write a new Lesson about this concept using the form
    below.'''
    edges = (
            dict(name='create_UnitLesson', toNode='END', title='Added a lesson'),
        )

class END(object):
    # node specification data goes here
    path = 'ct:ul_tasks'
    title = 'Done writing new lesson'
    help = '''Thanks for writing this new Lesson!
    See below for suggested next steps on concepts you can study in
    this courselet.'''

        
def get_specs():
    'get FSM specifications stored in this file'
    from fsmspec import FSMSpecification
    spec = FSMSpecification(name='add_lesson', hideTabs=True,
            title='Add a New Lesson',
            description='''Guides you through the steps of adding a new
            lesson to this courselet''',
            pluginNodes=[START, SEARCH, CONCEPTS, WRITE, END],
            fsmGroups=('teach/unit_tasks',),
        )
    return (spec,)

