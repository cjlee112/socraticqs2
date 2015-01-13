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
nodeDict = dict(START=dict(title='start here', path='/ct/',
                           funcName='testme.trivial'),
                END=dict(title='end here', path='/ct/nowhere'),
    )
edgeDict = (
    dict(name='next', fromNode='START', toNode='END', title='go go go'),
    )

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
    def test_load(self):
        'check loading an FSM graph, and replacing it'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        self.assertEqual(f.fsmnode_set.count(), 2)
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
        fsmData = dict(unit=self.unit, foo='bar')
        request = FakeRequest(self.user)
        fsmStack = fsm.FSMStack(request)
        self.assertIsNone(fsmStack.state)
        try:
            result = fsmStack.push(request, 'invalid', stateData=fsmData)
        except FSM.DoesNotExist:
            pass
        else:
            raise AssertionError('failed to catch bad FSM query')
        result = fsmStack.push(request, 'test', stateData=fsmData)
        self.assertEqual(request.session['fsmID'], fsmStack.state.pk)
        self.assertEqual(fsmStack.state.load_json_data(), fsmData)
        self.assertEqual(result.url, '/ct/')
    def test_trivial_plugin(self):
        'check trivial plugin import and call'
        f = FSM.save_graph(fsmDict, nodeDict, edgeDict, 'jacob')
        self.assertEqual(f.startNode.call_plugin(0, 0, 0), 'trivial result')
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
            
            
