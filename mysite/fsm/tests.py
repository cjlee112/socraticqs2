from django.contrib.auth.models import User

from fsm.fsm_base import FSMStack
from fsm.models import (
    FSM,
    FSMNode,
    FSMState,
    ActivityLog,
    JSONBlobMixin
)
from ct.models import (
    Course,
    Unit,
    Lesson,
    UnitLesson,
    Response,
    DONE_STATUS
)
from ct.tests import (
    FakeRequest,
    OurTestCase,
    create_question_unit
)


def load_fsm2(username):
    'load an FSM that displays a standard node page'
    fsmDict = dict(name='test2', title='try this')
    nodeDict = dict(
        START=dict(
            title='Welcome, Stranger',
            path='fsm:fsm_node',
            description='Thanks for your valuable input!'
        ),
        END=dict(title='end here', path='ct:home'),
    )
    edgeDict = (
        dict(
            name='next',
            fromNode='START',
            toNode='END',
            title='Write an Amazing Question',
            description='''Your mission, should you choose to accept it,
                        is to write an amazing question that yields wonderful insights.'''
        ),
    )
    return FSM.save_graph(fsmDict, nodeDict, edgeDict, username)


class FSMTests(OurTestCase):
    """
    Tests for FSM stack.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='jacob', email='jacob@_', password='top_secret'
        )
        # have to login or Django self.client.session storage won't work
        self.client.login(username='jacob', password='top_secret')
        self.course = Course(
            title='Great Course', description='the bestest', addedBy=self.user
        )
        self.course.save()
        self.unit = Unit(title='My Courselet', addedBy=self.user)
        self.unit.save()
        self.lesson = Lesson(
            title='Big Deal', text='very interesting info', addedBy=self.user
        )
        self.lesson.save_root()
        self.unitLesson = UnitLesson.create_from_lesson(
            self.lesson, self.unit, order='APPEND'
        )
        self.ulQ = create_question_unit(self.user)
        self.ulQ2 = create_question_unit(
            self.user, 'Pretest', 'Scary Question', 'Tell me something.'
        )
        self.json_mixin = JSONBlobMixin()
        self.fsmDict = dict(name='test', title='try this')
        self.nodeDict = dict(
            START=dict(title='start here', path='ct:home', funcName='fsm.fsm_plugin.testme.START'),
            MID=dict(title='in the middle', path='ct:about', doLogging=True),
            END=dict(title='end here', path='ct:home')
        )
        self.edgeDict = (
            dict(name='next', fromNode='START', toNode='END', title='go go go'),
            dict(name='select_Lesson', fromNode='MID', toNode='MID', title='go go go'),
        )

    def test_load(self):
        """
        Check loading an FSM graph, and replacing it.
        """
        f = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')
        self.assertEqual(f.fsmnode_set.count(), 3)
        self.assertEqual(f.startNode.name, 'START')
        self.assertEqual(f.startNode.outgoing.count(), 1)
        e = f.startNode.outgoing.all()[0]
        self.assertEqual(e.name, 'next')
        self.assertEqual(e.toNode.name, 'END')
        f2 = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')  # replace
        self.assertEqual(FSM.objects.get(pk=f.pk).name, 'testOLD')  # renamed
        self.assertNotEqual(f.startNode, f2.startNode)
        self.assertEqual(f.startNode.name, f2.startNode.name)

    def test_json_blob(self):
        """
        Check roundtrip dump/load via json blob data.
        """
        name, pk = self.json_mixin.dump_json_id(self.unit)
        label, obj = self.json_mixin.load_json_id(name, pk)
        self.assertEqual(self.unit, obj)
        self.assertEqual(label, 'Unit')

    def test_json_blob2(self):
        """
        Check roundtrip dump/load via named json blob data.
        """
        name, pk = self.json_mixin.dump_json_id(self.unit, 'fruity')
        self.assertEqual(name, 'fruity_Unit_id')
        label, obj = self.json_mixin.load_json_id(name, pk)
        self.assertEqual(self.unit, obj)
        self.assertEqual(label, 'fruity')

    def test_json_blob3(self):
        """
        Check roundtrip dump/load via json blob string.
        """
        s = self.json_mixin.dump_json_id_dict(dict(fruity=self.unit))
        d = self.json_mixin.load_json_id_dict(s)
        self.assertEqual(d.items(), [('fruity', self.unit)])

    def test_json_blob4(self):
        """
        Check roundtrip dump/load via db storage.
        """
        f = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')
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
        """
        Check basic startup of new FSM instance.
        """
        f = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')
        self.do_start(f)

    def test_start2(self):
        """
        Check basic startup of new FSM instance using FSMSpecification.
        """
        from fsm.fsm_plugin.testme import get_specs
        spec = get_specs()[0]
        f = spec.save_graph('jacob')
        self.assertTrue(f.startNode.doLogging)
        self.assertFalse(f.get_node('MID').doLogging)
        fsmStack = self.do_start(f)
        # test filter_input() plugin functionality
        edge = fsmStack.state.fsmNode.outgoing.get(name='next')
        self.assertTrue(edge.filter_input('the right stuff'))
        self.assertFalse(edge.filter_input('the WRONG stuff'))
        # test get_help() plugin functionality
        request = FakeRequest(self.user, path='/ct/about/')
        msg = fsmStack.state.fsmNode.get_help(fsmStack.state, request)
        self.assertEqual(msg, 'here here!')
        request = FakeRequest(self.user, path='/ct/courses/1/')
        msg = fsmStack.state.fsmNode.get_help(fsmStack.state, request)
        self.assertEqual(msg, 'there there')
        request = FakeRequest(self.user)
        msg = fsmStack.state.fsmNode.get_help(fsmStack.state, request)
        self.assertEqual(msg, None)

    def test_start3(self):
        """
        Check that FSMState saves unitLesson, select_ data, and logging.
        """
        f = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')
        fsmStack = self.do_start(f, unitLesson=self.unitLesson)
        self.assertEqual(fsmStack.state.unitLesson, self.unitLesson)
        request = FakeRequest(self.user, method='GET')
        # check logging on the MID node
        fsmStack.event(request, None)  # send a render event to log
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
        """
        Run tests of basic startup of new FSM instance.
        """
        fsmData = dict(unit=self.unit, foo='bar')
        request = FakeRequest(self.user)
        fsmStack = FSMStack(request)
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
        self.assertEqual(fsmStack.state.fsmNode.get_path(
            fsmStack.state, request
        ), '/ct/about/')
        self.assertEqual(result, '/ct/about/')
        return fsmStack

    def test_trivial_plugin(self):
        """
        Check trivial plugin import and call.
        """
        f = FSM.save_graph(self.fsmDict, self.nodeDict, self.edgeDict, 'jacob')
        request = FakeRequest(self.user)
        fsmStack = FSMStack(request)
        fsmStack.state = FSMState(user=self.user, fsmNode=f.startNode)
        self.assertEqual(f.startNode.event(fsmStack, request, 'start'),
                         '/ct/about/')
        self.assertEqual(f.startNode.get_path(fsmStack.state, request),
                         '/ct/some/where/else/')

    def test_bad_funcName(self):
        """
        Check that FSM.save_graph() catches bad plugin funcName.
        """
        nodeDictBad = dict(
            START=dict(title='start here', path='ct:home', funcName='fsm.fsm_plugin.testme.invalid')
        )
        try:
            FSM.save_graph(self.fsmDict, nodeDictBad, (), 'jacob')
        except AttributeError:
            pass
        else:
            raise AssertionError('FSM.save_graph() failed to catch bad plugin funcName')

    def test_bad_fsmID(self):
        """
        Make sure FSMStack silently handles bad fsmID.
        """
        request = FakeRequest(self.user, dict(fsmID=99))
        fsmStack = FSMStack(request)
        self.assertEqual(request.session, {})
        self.assertIsNone(fsmStack.state)

    def test_randomtrial(self):
        """
        Basic randomized trial.
        """
        self.assertEqual(self.ulQ.order, 0)
        from ct.fsm_plugin.lessonseq import get_specs
        f = get_specs()[0].save_graph(self.user.username)  # load FSM spec
        from ct.fsm_plugin.randomtrial import get_specs
        f = get_specs()[0].save_graph(self.user.username)  # load FSM spec
        self.assertEqual(ActivityLog.objects.count(), 0)
        fsmData = dict(testFSM='lessonseq', treatmentFSM='lessonseq',
                       treatment1=self.ulQ.unit, treatment2=self.ulQ.unit,
                       testUnit=self.ulQ2.unit, course=self.course)
        request, fsmStack, result = self.get_fsm_request(
            'randomtrial', fsmData, dict(trialName='test')
        )
        self.assertEqual(self.client.session['fsmID'], fsmStack.state.pk)
        self.assertEqual(result, '/fsm/nodes/%d/' % f.startNode.pk)
        self.assertEqual(ActivityLog.objects.count(), 1)
        # rt FSM start page
        response = self.client.get(result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'answer a few preliminary questions')
        url = '/ct/courses/%d/units/%d/lessons/%d/ask/' \
              % (self.course.pk, self.ulQ2.unit.pk, self.ulQ2.pk)
        self.check_post_get(result, dict(fsmtask='next'), url, 'Scary Question')
        # pretest Q
        postdata = dict(text='i dunno', confidence=Response.GUESS)
        url = self.check_post_get(url, postdata, '/assess/', 'write an answer')
        # pretest assess
        assessPOST = dict(selfeval=Response.CORRECT, status=DONE_STATUS, liked='')
        url2 = '/ct/courses/%d/units/%d/lessons/%d/ask/' \
               % (self.course.pk, self.ulQ.unit.pk, self.ulQ.pk)
        self.check_post_get(url, assessPOST, url2, 'your quest')
        # treatment Q
        postdata = dict(text='i like rats', confidence=Response.GUESS)
        url = self.check_post_get(url2, postdata, '/assess/', 'write an answer')
        # treatment assess
        url2 = '/ct/courses/%d/units/%d/lessons/%d/ask/' \
               % (self.course.pk, self.ulQ2.unit.pk, self.ulQ2.pk)
        self.check_post_get(url, assessPOST, url2, 'Scary Question')
        # posttest Q
        postdata = dict(text='i still dunno', confidence=Response.GUESS)
        url = self.check_post_get(url2, postdata, '/assess/', 'write an answer')
        # posttest assess
        url2 = '/ct/courses/%d/units/%d/tasks/' \
               % (self.course.pk, self.ulQ.unit.pk)
        self.check_post_get(url, assessPOST, url2, 'Next Step to work on')
        self.assertEqual(Response.objects.filter(activity__isnull=False,
                                                 confidence=Response.GUESS).
                         count(), 3)  # check responses logged to RT activity

    def test_slideshow(self):
        """
        Basic slide show FSM.
        """
        from ct.fsm_plugin.slideshow import get_specs
        get_specs()[0].save_graph(self.user.username)  # load FSM spec
        fsmData = dict(unit=self.ulQ2.unit, course=self.course)
        request, fsmStack, result = self.get_fsm_request('slideshow', fsmData)
        self.assertEqual(result, '/ct/courses/%d/units/%d/lessons/%d/read/'
              % (self.course.pk, self.ulQ2.unit.pk, self.ulQ2.pk))
        # start page = question
        response = self.client.get(result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scary Question')
        # answer page
        answer = self.ulQ2.get_answers()[0]
        url = '/ct/courses/%d/units/%d/lessons/%d/read/' \
              % (self.course.pk, self.ulQ2.unit.pk, answer.pk)
        self.check_post_get(result, dict(fsmtask='next'), url, 'an answer')
        # end of slide show should dump us on concepts page
        url2 = '/ct/courses/%d/units/%d/concepts/' % (self.course.pk, self.ulQ2.unit.pk)
        self.check_post_get(url, dict(fsmtask='next'), url2, 'Pretest')

    def get_fsm_request(self, fsmName, stateData, startArgs=None, **kwargs):
        """
        Create request, fsmStack and start specified FSM.
        """
        startArgs = startArgs or {}
        request = FakeRequest(self.user)
        request.session = self.client.session
        fsmStack = FSMStack(request)
        result = fsmStack.push(request, fsmName, stateData, startArgs, **kwargs)
        request.session.save()
        return request, fsmStack, result
