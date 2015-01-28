"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.http import HttpResponseRedirect
from ct.models import *
from ct import views, fsm

class ConceptMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jacob', email='jacob@_',
                                             password='top_secret')
        self.wikiUser = User.objects.create_user(username='wikipedia', email='wiki@_',
                                             password='top_secret')
        self.unit = Unit(title='My Courselet', addedBy=self.user)
        self.unit.save()
    def test_sourceDB(self):
        'check wikipedia concept retrieval'
        c, lesson = Concept.get_from_sourceDB('New York City', self.user)
        self.assertEqual(c.title, 'New York City')
        self.assertEqual(c.addedBy, self.user)
        self.assertEqual(lesson.addedBy, self.wikiUser)
        self.assertEqual(lesson.concept, c)
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertEqual(lesson.sourceID, 'New York City')
        self.assertIn('City of New York', lesson.text)
        # check that subsequent retrieval uses stored db record
        c2, l2 = Concept.get_from_sourceDB('New York City', self.user)
        self.assertEqual(c2.pk, c.pk)
        self.assertEqual(l2.pk, lesson.pk)
        self.assertIn(c, list(Concept.search_text('new york')))
    def test_new_concept(self):
        'check standard creation of a concept bound to a UnitLesson'
        title = 'Important Concept'
        text = 'This concept is very important.'
        concept = Concept.new_concept(title, text, self.unit, self.user)
        self.assertEqual(concept.title, title)
        self.assertFalse(concept.isError)
        lesson = Lesson.objects.get(concept=concept)
        self.assertEqual(lesson.text, text)
        self.assertEqual(lesson.kind, Lesson.BASE_EXPLANATION)
        ul = UnitLesson.objects.get(lesson=lesson)
        self.assertIs(ul.order, None)
        self.assertEqual(ul.treeID, lesson.treeID)
        self.assertEqual(ul.kind, UnitLesson.COMPONENT)
        # check creation of error model
        concept = Concept.new_concept(title, text, self.unit, self.user,
                                      isError=True)
        self.assertTrue(concept.isError)
        lesson = Lesson.objects.get(concept=concept)
        self.assertEqual(lesson.kind, Lesson.ERROR_MODEL)
        ul = UnitLesson.objects.get(lesson=lesson)
        self.assertEqual(ul.kind, UnitLesson.MISUNDERSTANDS)
    def test_error_models(self):
        'check creation and copying of error models'
        concept = Concept.new_concept('big', 'idea', self.unit, self.user)
        emUL1 = views.create_error_ul(Lesson(title='oops', addedBy=self.user,
                                    text='foo'), concept, self.unit, None)
        emUL2 = views.create_error_ul(Lesson(title='oops', addedBy=self.user,
                                    text='foo'), concept, self.unit, None)
        parent = UnitLesson.objects.get(lesson__concept=concept)
        ulList = concept.copy_error_models(parent)
        self.assertEqual(len(ulList), 2)
        lessons = [ul.lesson for ul in ulList]
        self.assertIn(emUL1.lesson, lessons)
        self.assertIn(emUL2.lesson, lessons)
        self.assertEqual(parent, ulList[0].parent)
        self.assertEqual(parent, ulList[1].parent)
        # test copying parent to a new unit
        unit3 = Unit(title='Another Courselet', addedBy=self.user)
        unit3.save()
        ul3 = parent.copy(unit3, self.user)
        self.assertEqual(ul3.unit, unit3)
        children = list(ul3.get_errors())
        self.assertEqual(len(children), 2)
        lessons = [ul.lesson for ul in children]
        self.assertIn(emUL1.lesson, lessons)
        self.assertIn(emUL2.lesson, lessons)
    def test_get_conceptlinks(self):
        'test ConceptLink creation and retrieval'
        concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        l1 = Lesson(title='ugh', text='brr', addedBy=self.user)
        l1.save_root(concept)
        ul1 = UnitLesson.create_from_lesson(l1, self.unit)
        l2 = Lesson(title='foo', text='bar', addedBy=self.user,
                    kind=Lesson.ORCT_QUESTION)
        l2.save_root(concept)
        ul2 = UnitLesson.create_from_lesson(l2, self.unit)
        # create a second commit of this lesson in a different unit
        l3 = Lesson(title='wunder', text='bar', addedBy=self.user,
                    kind=Lesson.ORCT_QUESTION, treeID=l2.treeID)
        l3.save_root(concept)
        unit3 = Unit(title='Another Courselet', addedBy=self.user)
        unit3.save()
        ul3 = UnitLesson.create_from_lesson(l3, unit3)
        clList = concept.get_conceptlinks(self.unit) # should get l1, l2
        self.assertEqual(len(clList), 2)
        self.assertEqual([cl for cl in clList if cl.lesson == l1][0]
                         .relationship, ConceptLink.DEFINES)
        self.assertEqual([cl for cl in clList if cl.lesson == l2][0]
                         .relationship, ConceptLink.TESTS)
        self.assertEqual(distinct_subset([ul1, ul2, ul3]), [ul1, ul2])



class LessonMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jacob', email='jacob@_',
                                             password='top_secret')
    def test_creation_treeID(self):
        'treeID properly initialized to default?'
        lesson = Lesson(title='foo', text='bar', addedBy=self.user)
        lesson.save_root()
        l2 = Lesson.objects.get(pk=lesson.pk)
        self.assertEqual(l2.treeID, l2.pk)

    def test_search_sourceDB(self):
        'check wikipedia search'
        results = Lesson.search_sourceDB('new york city')
        self.assertTrue(len(results) >= 10)
        self.assertIn('New York City', [t[0] for t in results])
        self.assertEqual(len(results[0]), 3)
        

fsmDict = dict(name='test', title='try this')
nodeDict = dict(START=dict(title='start here', path='ct:home',
                           funcName='testme.START'),
                MID=dict(title='in the middle', path='ct:about', doLogging=True),
                END=dict(title='end here', path='ct:home'),
    )
edgeDict = (
    dict(name='next', fromNode='START', toNode='END', title='go go go'),
    dict(name='select_Lesson', fromNode='MID', toNode='MID', title='go go go'),
    )

def load_fsm2(username):
    'load an FSM that displays a standard node page'
    fsmDict = dict(name='test2', title='try this')
    nodeDict = dict(START=dict(title='Welcome, Stranger', path='ct:fsm_node',
                               description='Thanks for your valuable input!'),
                    END=dict(title='end here', path='ct:home'),
        )
    edgeDict = (
        dict(name='next', fromNode='START', toNode='END',
             title='Write an Amazing Question',
             description='''Your mission, should you choose to accept it,
             is to write an amazing question that yields wonderful insights.'''),
        )
    return FSM.save_graph(fsmDict, nodeDict, edgeDict, username)

    
class FakeRequest(object):
    'trivial holder for request data to pass to test calls'
    def __init__(self, user, sessionDict=None, method='POST', dataDict=None):
        self.user = user
        self.method = method
        if not sessionDict:
            sessionDict = {}
        self.session = sessionDict
        if not dataDict:
            dataDict = {}
        setattr(self, method, dataDict)
            
class FSMTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jacob', email='jacob@_',
                                             password='top_secret')
        self.unit = Unit(title='My Courselet', addedBy=self.user)
        self.unit.save()
        self.lesson = Lesson(title='Big Deal', text='very interesting info',
                             addedBy=self.user)
        self.lesson.save_root()
        self.unitLesson = UnitLesson.create_from_lesson(self.lesson, self.unit)
    def test_load(self):
        'check loading an FSM graph, and replacing it'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        self.assertEqual(f.fsmnode_set.count(), 3)
        self.assertEqual(f.startNode.name, 'START')
        self.assertEqual(f.startNode.outgoing.count(), 1)
        e = f.startNode.outgoing.all()[0]
        self.assertEqual(e.name, 'next')
        self.assertEqual(e.toNode.name, 'END')
        f2 = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob') # replace
        self.assertEqual(FSM.objects.get(pk=f.pk).name, 'testOLD') # renamed
        self.assertNotEqual(f.startNode, f2.startNode)
        self.assertEqual(f.startNode.name, f2.startNode.name)
    def test_json_blob(self):
        'check roundtrip dump/load via json blob data'
        name, pk = dump_json_id(self.unit)
        label, obj = load_json_id(name, pk)
        self.assertEqual(self.unit, obj)
        self.assertEqual(label, 'Unit')
    def test_json_blob2(self):
        'check roundtrip dump/load via named json blob data'
        name, pk = dump_json_id(self.unit, 'fruity')
        self.assertEqual(name, 'fruity_Unit_id')
        label, obj = load_json_id(name, pk)
        self.assertEqual(self.unit, obj)
        self.assertEqual(label, 'fruity')
    def test_json_blob3(self):
        'check roundtrip dump/load via json blob string'
        s = dump_json_id_dict(dict(fruity=self.unit))
        d = load_json_id_dict(s)
        self.assertEqual(d.items(), [('fruity', self.unit)])
    def test_json_blob4(self):
        'check roundtrip dump/load via db storage'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        d = f.startNode.load_json_data()
        self.assertEqual(d, {})
        d['fruity'] = self.unit
        d['anumber'] = 3
        d['astring'] = 'jeff'
        f.startNode.save_json_data(d)
        node = FSMNode.objects.get(pk=f.startNode.pk)
        d2 = node.load_json_data()
        self.assertEqual(d2, {'fruity': self.unit, 'anumber': 3,
                              'astring': 'jeff'})
    def test_start(self):
        'check basic startup of new FSM instance'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        self.do_start(f)
    def test_start2(self):
        'check basic startup of new FSM instance using FSMSpecification'
        from ct.fsm_plugin.testme import get_specs
        spec = get_specs()[0]
        f = spec.save_graph('jacob')
        self.do_start(f)
    def test_start3(self):
        'check that FSMState saves unitLesson, select_ data, and logging'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        fsmStack = self.do_start(f, unitLesson=self.unitLesson)
        self.assertEqual(fsmStack.state.unitLesson, self.unitLesson)
        request = FakeRequest(self.user, method='GET')
        # check logging on the MID node
        fsmStack.event(request, None) # send a render event to log
        self.assertEqual(fsmStack.state.activity.fsmName, 'test')
        ae = fsmStack.state.activityEvent
        self.assertEqual(ae.nodeName, 'MID')
        self.assertEqual(ae.unitLesson, self.unitLesson)
        self.assertIsNotNone(ae.startTime)
        self.assertIsNone(ae.endTime)
        request = FakeRequest(self.user)
        # now try a select_ event
        fsmStack.event(request, 'select_Lesson', lesson=self.lesson)
        self.assertEqual(fsmStack.state.get_data_attr('lesson'), self.lesson)
        # check that exit from MID node was logged
        self.assertIsNotNone(ae.endTime)
        self.assertTrue(ae.endTime > ae.startTime)
        self.assertEqual(ae.exitEvent, 'select_Lesson')
        self.assertIsNone(fsmStack.state.activityEvent)
    def do_start(self, f, **kwargs):
        'run tests of basic startup of new FSM instance'
        fsmData = dict(unit=self.unit, foo='bar')
        request = FakeRequest(self.user)
        fsmStack = fsm.FSMStack(request)
        self.assertIsNone(fsmStack.state)
        try:
            result = fsmStack.push(request, 'invalid', stateData=fsmData, **kwargs)
        except FSM.DoesNotExist:
            pass
        else:
            raise AssertionError('failed to catch bad FSM query')
        result = fsmStack.push(request, 'test', stateData=fsmData, **kwargs)
        self.assertEqual(request.session['fsmID'], fsmStack.state.pk)
        self.assertEqual(fsmStack.state.load_json_data(), fsmData)
        self.assertEqual(fsmStack.state.fsmNode.name, 'MID')
        self.assertEqual(fsmStack.state.fsmNode.path, 'ct:about')
        self.assertEqual(fsmStack.state.fsmNode.get_path(0, 0), '/ct/about/')
        self.assertEqual(result, '/ct/about/')
        return fsmStack
    def test_trivial_plugin(self):
        'check trivial plugin import and call'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        request = FakeRequest(self.user)
        fsmStack = fsm.FSMStack(request)
        fsmStack.state = FSMState(user=self.user, fsmNode=f.startNode)
        self.assertEqual(f.startNode.event(fsmStack, 0, 'start'), '/ct/about/')
        self.assertEqual(f.startNode.get_path(0, 0), '/ct/some/where/else/')
    def test_bad_funcName(self):
        'check that FSM.save_graph() catches bad plugin funcName'
        edgeDictBad = (
            dict(name='next', fromNode='START', toNode='END',
                 funcName='testme.invalid', title='go go go'),
        )
        try:
            f = FSM.save_graph(fsmDict, nodeDict, edgeDictBad, 'jacob')
        except AttributeError:
            pass
        else:
            raise AssertionError('FSM.save_graph() failed to catch bad plugin funcName')
    def test_bad_fsmID(self):
        'make sure FSMStack silently handles bad fsmID'
        request = FakeRequest(self.user, dict(fsmID=99))
        fsmStack = fsm.FSMStack(request)
        self.assertEqual(request.session, {})
        self.assertIsNone(fsmStack.state)
        
