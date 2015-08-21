"""
Unit tests for core app models.py.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from mock import Mock, patch

from ct.models import *
from ct.sourcedb_plugin.wikipedia_plugin import LessonDoc


class ConceptTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.concept = Concept(title='test title', addedBy=self.user)
        self.concept.save()
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(
            unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id
        )
        self.unit_lesson.save()

    def test_title(self):
        self.assertTrue(isinstance(self.concept, Concept))
        self.assertEqual(self.concept.__unicode__(), self.concept.title)

    @patch('ct.models.Lesson.get_from_sourceDB')
    def test_get_from_sourceDB(self, get_from_sourceDB):
        lesson = Mock()
        lesson.concept = False
        lesson.title = 'Test title'
        get_from_sourceDB.return_value = lesson
        result = Concept.get_from_sourceDB('Test title', self.user)
        self.assertIsInstance(result[0], Concept)
        self.assertEqual(result[1], lesson)
        self.assertEqual(result[0].title, 'Test title')
        self.assertEqual(result[1].title, 'Test title')
        self.assertEqual(lesson.concept, result[0])
        self.assertEqual(result[0].addedBy, self.user)

    @patch('ct.models.Lesson.get_from_sourceDB')
    def test_get_from_sourceDB_find_by_lesson(self, get_from_sourceDB):
        concept = Mock()
        lesson = Mock()
        lesson.concept = concept
        lesson.title = 'Test title'
        get_from_sourceDB.return_value = lesson
        result = Concept.get_from_sourceDB('Test title', self.user)
        self.assertEqual(result, (concept, lesson))

    def test_search_text(self):
        dublicate_concept = Concept(title='test title', addedBy=self.user)
        dublicate_concept.save
        result = Concept.search_text('test title')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, self.concept.title)

    @patch('ct.models.timezone')
    def test_new_concept(self, timezone_patched):
        patched_time = str(timezone.now())
        timezone_patched.now.return_value = patched_time
        result = Concept.new_concept('new concept title', 'new concept text', self.unit, self.user)
        self.assertIsInstance(result, Concept)
        self.assertEqual(result.addedBy, self.user)
        self.assertEqual(result.title, 'new concept title')
        created_lesson = Lesson.objects.filter(concept=result).first()
        created_unit_lesson = UnitLesson.objects.filter(lesson__title='new concept title').first()
        self.assertTrue(created_lesson)
        self.assertTrue(created_unit_lesson)
        self.assertEqual(created_lesson.title, result.title)
        self.assertEqual(created_lesson.text, 'new concept text')
        self.assertEqual(created_lesson.addedBy, self.user)
        self.assertEqual(created_lesson.changeLog, 'initial commit')
        self.assertEqual(str(created_lesson.commitTime), patched_time)
        self.assertEqual(created_lesson.concept, result)
        self.assertEqual(created_unit_lesson.lesson, created_lesson)
        self.assertEqual(created_unit_lesson.unit, self.unit)

    @patch('ct.models.timezone')
    def test_new_concept_isError(self, timezone_patched):
        patched_time = str(timezone.now())
        timezone_patched.now.return_value = patched_time
        result = Concept.new_concept('new concept title', 'new concept text', self.unit, self.user, isError=True)
        self.assertIsInstance(result, Concept)
        self.assertEqual(result.addedBy, self.user)
        self.assertEqual(result.title, 'new concept title')
        created_lesson = Lesson.objects.filter(concept=result).first()
        created_unit_lesson = UnitLesson.objects.filter(lesson__title='new concept title').first()
        self.assertTrue(created_lesson)
        self.assertTrue(created_unit_lesson)
        self.assertEqual(created_lesson.title, result.title)
        self.assertEqual(created_lesson.text, 'new concept text')
        self.assertEqual(created_lesson.addedBy, self.user)
        self.assertEqual(created_lesson.changeLog, 'initial commit')
        self.assertEqual(str(created_lesson.commitTime), patched_time)
        self.assertEqual(created_lesson.concept, result)
        self.assertEqual(created_unit_lesson.lesson, created_lesson)
        self.assertEqual(created_unit_lesson.unit, self.unit)

        self.assertTrue(result.isError)
        self.assertEqual(created_lesson.kind, Lesson.ERROR_MODEL)

    def test_create_error_model(self):
        result = self.concept.create_error_model(self.user)
        self.assertIsInstance(result, Concept)
        self.assertTrue(result.isError)
        self.assertEqual(result.addedBy, self.user)
        created_concept_graph = ConceptGraph.objects.filter(
            toConcept=self.concept, fromConcept=result
        ).first()
        self.assertIsNotNone(created_concept_graph)
        self.assertEqual(created_concept_graph.addedBy, self.user)
        self.assertEqual(created_concept_graph.relationship, ConceptGraph.MISUNDERSTANDS)

    def test_copy_error_models(self):
        self.lesson.kind = Lesson.ERROR_MODEL
        em = self.concept.create_error_model(
            title=self.lesson.title, addedBy=self.user
        )
        self.lesson.concept = em
        self.lesson.save_root()
        UnitLesson.create_from_lesson(self.lesson, self.unit, parent=self.unit_lesson)
        result = self.concept.copy_error_models(self.unit_lesson)
        self.assertIsInstance(result[0], UnitLesson)
        self.assertEqual(result[0].lesson, self.lesson)
        self.assertEqual(result[0].unit, self.unit)
        self.assertEqual(result[0].kind, UnitLesson.MISUNDERSTANDS)
        self.assertEqual(result[0].parent, self.unit_lesson)

    def test_get_url(self):
        base_path = reverse('ct:study_unit', args=(self.course.id, self.unit.id))
        result = self.concept.get_url(base_path)
        self.assertEqual(
            result,
            reverse('ct:concept_lessons_student', args=(self.course.id, self.unit.id, self.unit_lesson.id))
        )

    def test_get_url_isError(self):
        self.concept.isError = True
        base_path = reverse('ct:study_unit', args=(self.course.id, self.unit.id))
        result = self.concept.get_url(base_path)
        self.assertEqual(
            result,
            reverse('ct:resolutions_student', args=(self.course.id, self.unit.id, self.unit_lesson.id))
        )

    def test_get_url_subpath(self):
        base_path = reverse('ct:study_unit', args=(self.course.id, self.unit.id))
        result = self.concept.get_url(base_path, subpath='faq')
        self.assertEqual(
            result,
            reverse('ct:concept_faq_student', args=(self.course.id, self.unit.id, self.unit_lesson.id))
        )

    def test_get_url_subpath_empty(self):
        base_path = reverse('ct:study_unit', args=(self.course.id, self.unit.id))
        result = self.concept.get_url(base_path, subpath='')
        self.assertEqual(
            result,
            reverse('ct:study_concept', args=(self.course.id, self.unit.id, self.unit_lesson.id))
        )

    def test_get_error_tests(self):
        self.misunderstand_ul = UnitLesson.create_from_lesson(
            self.lesson,
            self.unit,
            kind=UnitLesson.MISUNDERSTANDS,
            parent=self.unit_lesson
        )
        result = self.concept.get_error_tests()
        self.assertEqual(result[0], self.unit_lesson)

    def test_get_conceptlinks(self):
        result = self.concept.get_conceptlinks(self.unit)
        self.assertIsInstance(result[0], ConceptLink)
        self.assertEqual(result[0].unitLesson, self.unit_lesson)

    def test_get_conceptlinks_two_ul(self):
        cl2 = ConceptLink(
            concept=self.concept, lesson=self.lesson, relationship=ConceptLink.RESOLVES, addedBy=self.user
        )
        cl2.save()
        result = self.concept.get_conceptlinks(self.unit)
        self.assertIsInstance(result[0], ConceptLink)
        self.assertEqual(result[0].unitLesson, self.unit_lesson)
        self.assertEqual(result[1].unitLesson, self.unit_lesson)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].relationship, ConceptLink.RESOLVES)  # ConceptLink's are sorted by relationship


class ConceptGraphTest(TestCase):
    def test_init(self):
        user = User.objects.create_user(username='test', password='test')
        concept_from = Concept(title='test title', addedBy=user)
        concept_from.save()
        concept_to = Concept(title='test title2', addedBy=user)
        concept_to.save()
        concept_graph = ConceptGraph(
            fromConcept=concept_from,
            toConcept=concept_to,
            relationship=ConceptGraph.TESTS,
            addedBy=user,
            approvedBy=user
        )
        concept_graph.save()
        concept_graph = ConceptGraph.objects.filter(addedBy=user).first()
        self.assertEqual(concept_graph.fromConcept, concept_from)
        self.assertEqual(concept_graph.toConcept, concept_to)
        self.assertEqual(concept_graph.relationship, ConceptGraph.TESTS)
        self.assertEqual(concept_graph.addedBy, user)
        self.assertEqual(concept_graph.approvedBy, user)
        self.assertIsNotNone(concept_graph.atime)


class LessonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')

    def test_get_sourceDB_plugin(self):
        result = Lesson.get_sourceDB_plugin('wikipedia')
        self.assertEqual(result, LessonDoc)

    # Need to move to integrate tests - get data from wiki
    def test_get_from_sourceDB(self):
        lesson = Lesson.get_from_sourceDB('New York', self.user)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, self.user)
        self.assertEqual(lesson.title, 'New York')
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertTrue(Lesson.objects.filter(addedBy=self.user).exists())

    # Need to move to integrate tests - get data from wiki
    def test_get_from_sourceDB_noSave_wiki_user(self):
        user = User.objects.create_user(username='wikipedia', password='wiki')
        lesson = Lesson.get_from_sourceDB('New York', user, doSave=False)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, user)
        self.assertEqual(lesson.title, 'New York')
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertFalse(Lesson.objects.filter(addedBy=self.user).exists())

    @patch('ct.models.Lesson.get_sourceDB_plugin')
    def test_get_from_sourceDB_unittest(self, get_sourceDB_plugin):
        data = Mock()
        data.title = 'New York'
        data.url = '/test/url/'
        data.description = 'test Description'
        dataClass = Mock(return_value=data)
        get_sourceDB_plugin.return_value = dataClass
        lesson = Lesson.get_from_sourceDB('New York', self.user)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, self.user)
        self.assertEqual(lesson._sourceDBdata, data)
        self.assertEqual(lesson.title, data.title)
        self.assertEqual(lesson.text, data.description)
        self.assertEqual(lesson.url, data.url)
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertTrue(Lesson.objects.filter(addedBy=self.user).exists())
        get_sourceDB_plugin.assert_called_once_with('wikipedia')
        dataClass.assert_called_once_with(data.title)

    @patch('ct.models.Lesson.get_sourceDB_plugin')
    def test_get_from_sourceDB_noSave_wiki_user_unittest(self, get_sourceDB_plugin):
        user = User.objects.create_user(username='wikipedia', password='wiki')
        data = Mock()
        data.title = 'New York'
        data.description = '/test/url/'
        data.url = 'test Description'
        dataClass = Mock(return_value=data)
        get_sourceDB_plugin.return_value = dataClass
        lesson = Lesson.get_from_sourceDB('New York', user, doSave=False)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, user)
        self.assertEqual(lesson._sourceDBdata, data)
        self.assertEqual(lesson.title, data.title)
        self.assertEqual(lesson.text, data.description)
        self.assertEqual(lesson.url, data.url)
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertFalse(Lesson.objects.filter(addedBy=self.user).exists())
        get_sourceDB_plugin.assert_called_once_with('wikipedia')
        dataClass.assert_called_once_with(data.title)

    @patch('ct.models.Lesson.get_sourceDB_plugin')
    def test_search_sourceDB(self, get_sourceDB_plugin):
        query = Mock()
        dataClass = Mock()
        get_sourceDB_plugin.return_value = dataClass
        Lesson.search_sourceDB(query)
        dataClass.search.assert_called_once_with(query)

    def test_save_root(self):
        lesson = self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.assertIsNone(lesson.treeID)
        lesson.save_root()
        self.assertIsNotNone(lesson.treeID)

    def test_save_root_concept(self):
        concept = Concept(title='test title', addedBy=self.user)
        concept.save()
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, concept=concept)
        lesson.save_root(concept=concept, relationship=ConceptLink.TESTS)
        self.assertTrue(ConceptLink(concept=concept, addedBy=self.user, relationship=ConceptLink.TESTS))

    def test_save_root_concept_default_relation(self):
        concept = Concept(title='test title', addedBy=self.user)
        concept.save()
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, concept=concept)
        lesson.save_root(concept=concept)
        self.assertTrue(ConceptLink(concept=concept, addedBy=self.user, relationship=ConceptLink.DEFINES))

    def test_is_committed(self):
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, commitTime=timezone.now())
        lesson2 = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.assertTrue(lesson.is_committed())
        self.assertFalse(lesson2.is_committed())

    def test_clone_dict(self):
        concept = Concept(title='test title', addedBy=self.user)
        concept.save()
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, commitTime=timezone.now(), concept=concept)
        lesson.save_root(concept=concept, relationship=ConceptLink.TESTS)
        clone_attr_dict = lesson._clone_dict()
        for attr in Lesson._cloneAttrs:
            self.assertIn(attr, clone_attr_dict)
        self.assertEqual(clone_attr_dict['title'], 'ugh')
        self.assertEqual(clone_attr_dict['text'], 'brr')
        self.assertEqual(clone_attr_dict['concept'], concept)

    def test_checkout(self):
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, commitTime=timezone.now())
        result = lesson.checkout(self.user)
        self.assertIsInstance(result, Lesson)
        self.assertEqual(result.parent, lesson)
        cloned_dict = lesson._clone_dict()
        for attr in cloned_dict:
            self.assertEqual(getattr(result, attr), cloned_dict[attr])

    @patch('ct.models.Lesson.checkin')
    def test_checkout_do_checkin(self, checkin):
        new_user = User.objects.create_user(username='new user', password='new test')
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        lesson.checkout(new_user)
        checkin.assert_called_once_with(commit=True)

    @patch('ct.models.Lesson.conceptlink_set')
    @patch('ct.models.Lesson.save')
    def test_checkin_save(self, save, conceptlink_set):
        parent = Lesson(title='parent', text='parent', addedBy=self.user)
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, parent=parent)
        lesson.checkin(commit=False)
        save.assert_called_once_with()
        self.assertFalse(lesson.is_committed())

        save.reset_mock()

        lesson.checkin(commit=True)
        save.assert_called_with()
        self.assertTrue(lesson.is_committed())
        self.assertTrue(parent.is_committed())

        save.reset_mock()

        concept_link = Mock()
        conceptlink_set.all.return_value = [concept_link, concept_link]
        lesson.checkin(commit=False, copyLinks=True)
        concept_link.copy.assert_called_with(lesson)
        self.assertEqual(concept_link.copy.call_count, 2)

    def test_add_concept_link(self):
        concept = Concept(title='test title', addedBy=self.user)
        concept.save()
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        lesson.save()
        self.assertTrue(lesson.add_concept_link(concept, ConceptLink.TESTS, self.user))
        self.assertTrue(
            ConceptLink.objects.filter(concept=concept, addedBy=self.user, relationship=ConceptLink.TESTS).exists()
        )

    def test_title(self):
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.assertEqual(lesson.__unicode__(), lesson.title)


class ConceptLinkTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.concept = Concept(title='test title', addedBy=self.user)
        self.concept.save()
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.lesson.save_root()
        self.lesson.add_concept_link(self.concept, ConceptLink.TESTS, self.user)
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()

    def test_copy(self):
        lesson = Lesson(title='ugh test 2', text='brr test 2', addedBy=self.user)
        lesson.save()
        concept_link = self.lesson.conceptlink_set.get(lesson=self.lesson)
        concept_link_copied = concept_link.copy(lesson)
        self.assertTrue(ConceptLink.objects.filter(id=concept_link_copied.id).exists())
        concept_link_copied = ConceptLink.objects.get(id=concept_link_copied.id)
        self.assertIsInstance(concept_link_copied, ConceptLink)
        self.assertEqual(concept_link_copied.concept, self.concept)
        self.assertEqual(concept_link_copied.lesson, lesson)
        self.assertEqual(concept_link_copied.relationship, concept_link.relationship)
        self.assertEqual(concept_link_copied.addedBy, self.user)

    def test_annotate_ul(self):
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        concept_link = self.lesson.conceptlink_set.get(lesson=self.lesson)
        concept_link.annotate_ul(self.unit)
        self.assertIsNotNone(concept_link.unitLesson)

    def test_annotate_ul_raise_exception(self):
        concept_link = self.lesson.conceptlink_set.get(lesson=self.lesson)
        with self.assertRaises(UnitLesson.DoesNotExist):
            concept_link.annotate_ul(self.unit)


class StudyListTest(TestCase):
    def test_title(self):
        user = User.objects.create_user(username='test', password='test')
        lesson = Lesson(title='ugh', text='brr', addedBy=user)
        lesson.save()
        study_list = StudyList(lesson=lesson, user=user)
        self.assertEqual(study_list.__unicode__(), lesson.title)


class UnitLessonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.concept = Concept(title='test title', addedBy=self.user)
        self.concept.save()
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        self.lesson.save_root()
        self.lesson.add_concept_link(self.concept, ConceptLink.TESTS, self.user)
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()

    def test_create_from_lesson(self):
        result = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        self.assertIsInstance(result, UnitLesson)
        self.assertEqual(result.unit, self.unit)
        self.assertEqual(result.lesson, self.lesson)
        self.assertTrue(UnitLesson.objects.filter(unit=self.unit, lesson=self.lesson).exists())

    def test_create_from_lesson_answer(self):
        result = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson, addAnswer=True)
        self.assertIsInstance(result, UnitLesson)
        self.assertEqual(result.unit, self.unit)
        self.assertEqual(result.lesson, self.lesson)
        self.assertIsInstance(result._answer, UnitLesson)
        self.assertTrue(UnitLesson.objects.filter(unit=self.unit, lesson=self.lesson).exists())
        answer = Lesson.objects.filter(
            title='Answer', text='write an answer', addedBy=self.user, kind=Lesson.ANSWER
        ).first()
        self.assertTrue(UnitLesson.objects.filter(unit=self.unit, lesson=answer, parent=result).exists())

    @patch('ct.models.Unit.next_order', return_value=42)
    def test_create_from_lesson_order_append(self, next_order):
        result = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson, order='APPEND')
        next_order.assert_called_once_with()
        self.assertEqual(result.order, 42)

    def test_search_text(self):
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = UnitLesson.search_text('ugh')
        self.assertIsInstance(result[0], UnitLesson)
        result = UnitLesson.search_text('brr')
        self.assertIsInstance(result[0], UnitLesson)

    def test_search_text_lesson_is_lesson(self):
        self.lesson.kind = Lesson.BASE_EXPLANATION
        self.lesson.save()
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = UnitLesson.search_text('ugh', searchType='lesson')
        self.assertIsInstance(result[0], UnitLesson)
        self.assertEqual(result[0].lesson, self.lesson)
        self.assertEqual(result[0].unit, self.unit)

    def test_search_text_question(self):
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = UnitLesson.search_text('ugh', searchType='question')
        self.assertIsInstance(result[0], UnitLesson)
        self.assertEqual(result[0].lesson, self.lesson)
        self.assertEqual(result[0].unit, self.unit)

    def test_search_text_error(self):
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson, kind=UnitLesson.MISUNDERSTANDS)
        self.lesson.concept = self.concept
        self.lesson.save()
        result = UnitLesson.search_text('ugh', searchType=0)
        self.assertIsInstance(result[0], UnitLesson)
        self.assertEqual(result[0].lesson, self.lesson)
        self.assertEqual(result[0].unit, self.unit)

    @patch('ct.models.distinct_subset')
    def test_search_text_dedupe(self, distinct_subset):
        UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        UnitLesson.search_text('ugh', searchType='question', dedupe=True)
        self.assertEqual(distinct_subset.call_count, 1)

    @patch('ct.models.Lesson.search_sourceDB')
    def test_search_sourceDB(self, search_sourceDB):
        result_queries = (
            ('test query 1', 'test query 1', 'http:/test/path1'),
            ('test query 2', 'test query 2', 'http:/test/path2'),
        )
        search_sourceDB.return_value = result_queries
        self.lesson.sourceDB = 'wikipedia'
        self.lesson.sourceID = 'test query 1'
        self.lesson.save()
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = UnitLesson.search_sourceDB('test query', unit=self.unit)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ([unit_lesson], [('test query 2', 'test query 2', 'http:/test/path2')]))
        result = UnitLesson.search_sourceDB('test query')
        self.assertEqual(result, ([unit_lesson], [('test query 2', 'test query 2', 'http:/test/path2')]))

    def test_get_answers(self):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson_answer = UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.ANSWERS
        )
        result = unit_lesson.get_answers()
        self.assertIsInstance(result, QuerySet)
        self.assertEqual(result[0], unit_lesson_answer)
        # Redundant check
        with patch('ct.models.UnitLesson.unitlesson_set') as mocked:
            unit_lesson.get_answers()
            mocked.filter.assert_called_once_with(kind=UnitLesson.ANSWERS)

    def test_get_errors(self):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson_answer = UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.MISUNDERSTANDS
        )
        result = unit_lesson.get_errors()
        self.assertIsInstance(result, QuerySet)
        self.assertEqual(result[0], unit_lesson_answer)
        # Redundant check
        with patch('ct.models.UnitLesson.unitlesson_set') as mocked:
            unit_lesson.get_errors()
            mocked.filter.assert_called_once_with(kind=UnitLesson.MISUNDERSTANDS)

    def test_get_linked_concepts(self):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = unit_lesson.get_linked_concepts()
        self.assertIsInstance(result, QuerySet)
        self.assertEqual(result[0], ConceptLink.objects.filter(concept=self.concept).first())
        # Redundant check
        with patch('ct.models.Lesson.conceptlink_set') as mocked:
            unit_lesson.get_linked_concepts()
            mocked.all.assert_called_once_with()

    def test_get_concepts(self):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = unit_lesson.get_concepts()
        self.assertEqual(result[0], self.concept)
        with patch('ct.models.Concept.objects.filter') as mocked:
            unit_lesson.get_concepts()
            mocked.assert_called_once_with(
                conceptlink__lesson=self.lesson,
                isError=False
            )

    def test_get_em_resolutions(self):
        self.lesson.concept = self.concept
        self.lesson.save()
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson_resolves = UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.RESOLVES
        )
        result = unit_lesson.get_em_resolutions()
        self.assertEqual(result[0], self.concept)
        self.assertEqual(result[1][0], unit_lesson_resolves)

    @patch('ct.models.UnitLesson.response_set')
    def test_get_new_inquiries(self, response_set):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson.get_new_inquiries()
        response_set.filter.assert_called_once_with(
            kind=Response.STUDENT_QUESTION,
            needsEval=True
        )

    @patch('ct.models.UnitLesson.objects.filter')
    @patch('ct.models.distinct_subset')
    def test_get_alternative_defs(self, distinct_subset, mocked_filter):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson.get_alternative_defs()
        self.assertEqual(distinct_subset.call_count, 1)
        mocked_filter.assert_called_once_with(lesson__concept=unit_lesson.lesson.concept)
        mocked_filter().exclude.assert_called_once_with(treeID=unit_lesson.treeID)

    @patch('ct.models.Unit.unitlesson_set')
    def test_get_next_lesson(self, mocked):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        with self.assertRaises(UnitLesson.DoesNotExist):
            unit_lesson.get_next_lesson()
        unit_lesson.order = 1
        unit_lesson.get_next_lesson()
        mocked.get.assert_called_once_with(order=unit_lesson.order + 1)

    @patch('ct.models.Lesson.checkout')
    def test_checkout(self, checkout):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        result = unit_lesson.checkout(self.user)
        checkout.assert_called_once_with(self.user)
        self.assertEqual(result, checkout())
        checkout.return_value = False
        result = unit_lesson.checkout(self.user)
        self.assertEqual(result, unit_lesson.lesson)

    @patch('ct.models.Lesson.checkin')
    def test_checkin(self, mocked_checkin):
        lesson = Lesson(title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        lesson.save_root()
        lesson.changeLog = 'test change log'
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        with patch('ct.models.UnitLesson.save') as mocked_save:
            unit_lesson.checkin(lesson)
            mocked_checkin.assert_called_once_with(True, True, True)
            mocked_save.assert_called_with()
            self.assertEqual(unit_lesson.lesson, lesson)

    @patch('ct.models.Lesson.checkin')
    def test_checkin_same_lesson(self, mocked_checkin):
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        with patch('ct.models.UnitLesson.save') as mocked_save:
            mocked_checkin.reset_mock()
            mocked_save.reset_mock()
            unit_lesson.checkin(self.lesson)
            mocked_checkin.assert_called_once_with(None, True, False)
            self.assertEqual(mocked_save.call_count, 0)

            mocked_checkin.reset_mock()
            mocked_save.reset_mock()
            self.lesson.changeLog = 'new test change log'
            unit_lesson.checkin(self.lesson)
            mocked_checkin.assert_called_once_with(True, True, False)
            self.assertEqual(mocked_save.call_count, 0)

    def test_copy(self):
        unit = Unit(title='new test unit title', addedBy=self.user)
        unit.save()
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.RESOLVES
        )
        result = unit_lesson.copy(unit, self.user, order='APPEND')
        self.assertIsInstance(result, UnitLesson)
        self.assertEqual(result.order, 0)
        self.assertEqual(unit_lesson.lesson.changeLog, 'snapshot for fork by %s' % self.user.username)
        self.assertEqual(result.kind, unit_lesson.kind)
        self.assertEqual(result.lesson, unit_lesson.lesson)
        self.assertEqual(result.addedBy, unit_lesson.addedBy)
        self.assertNotEqual(result.unit, unit_lesson.unit)
        self.assertEqual(result.treeID, unit_lesson.treeID)
        self.assertEqual(result.branch, unit_lesson.branch)

    @patch('ct.models.Lesson.add_concept_link')
    def test_copy_resolves(self, add_concept_link):
        self.lesson.concept = self.concept
        self.lesson.save()
        unit = Unit(title='new test unit title', addedBy=self.user)
        unit.save()
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        resolve = UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.RESOLVES
        )
        resolve.copy(unit, self.user, parent=unit_lesson, kind=UnitLesson.RESOLVES)
        add_concept_link.assert_called_once_with(unit_lesson.lesson.concept, ConceptLink.RESOLVES, self.user)

    def test_save_resolution(self):
        self.lesson.concept = self.concept
        self.lesson.save()
        unit_lesson = UnitLesson.create_from_lesson(unit=self.unit, lesson=self.lesson)
        unit_lesson = UnitLesson.create_from_lesson(
            unit=self.unit, lesson=self.lesson, parent=unit_lesson, kind=UnitLesson.MISUNDERSTANDS
        )
        lesson = Lesson(title='relosution', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        lesson.save_root()
        result = unit_lesson.save_resolution(lesson)
        self.assertIsInstance(result, UnitLesson)
        self.assertEqual(result.lesson, lesson)
        self.assertEqual(result.unit, self.unit)
        self.assertEqual(result.kind, UnitLesson.RESOLVES)
        self.assertEqual(result.parent, unit_lesson)

    @patch('ct.models.UnitLesson.create_from_lesson')
    def test_save_resolution_unittest(self, create_from_lesson):
        """
        Pure unittest for save_resolution method.
        """
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42)
        unit_lesson.lesson = self.lesson
        self.lesson.concept = self.concept
        lesson = Mock()
        lesson.concept = Mock()
        with self.assertRaises(ValueError):
            unit_lesson.save_resolution(lesson)

        unit_lesson.kind = UnitLesson.MISUNDERSTANDS
        unit_lesson.save_resolution(lesson)
        lesson.save_root.assert_called_once_with(self.lesson.concept, ConceptLink.RESOLVES)
        create_from_lesson.assert_called_once_with(
            lesson, self.unit, kind=UnitLesson.RESOLVES, parent=unit_lesson
        )

    @patch('ct.models.UnitLesson.unitlesson_set')
    def test_copy_resolution(self, unitlesson_set):
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42)
        new_unit_lesson = Mock()
        new_unit_lesson.treeID = 43
        result = unit_lesson.copy_resolution(new_unit_lesson, self.user)
        unitlesson_set.get.assert_called_once_with(treeID=new_unit_lesson.treeID, kind=UnitLesson.RESOLVES)
        self.assertEqual(result, unit_lesson.unitlesson_set.get())

        unitlesson_set.get.side_effect = UnitLesson.DoesNotExist

        result = unit_lesson.copy_resolution(new_unit_lesson, self.user)
        new_unit_lesson.copy.assert_called_once_with(
            unit_lesson.unit, self.user, unit_lesson, kind=UnitLesson.RESOLVES
        )
        self.assertEqual(result, new_unit_lesson.copy())

    @patch('ct.models.UnitLesson.get_type', return_value=IS_LESSON)
    def test_get_url(self, get_type):
        course = Course(title='test_title', addedBy=self.user)
        course.save()
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42)
        unit_lesson.save()
        base_path = reverse('ct:study_unit', args=(course.id, self.unit.id))
        result = unit_lesson.get_url(base_path)
        self.assertEqual(result, reverse('ct:lesson', args=(course.id, self.unit.id, unit_lesson.id)))

        get_type.return_value = IS_CONCEPT
        result = unit_lesson.get_url(base_path)
        self.assertEqual(result, reverse('ct:concept_lessons_student', args=(course.id, self.unit.id, unit_lesson.id)))

        get_type.return_value = IS_ERROR
        result = unit_lesson.get_url(base_path)
        self.assertEqual(result, reverse('ct:resolutions_student', args=(course.id, self.unit.id, unit_lesson.id)))

        result = unit_lesson.get_url(base_path, forceDefault=True)
        self.assertEqual(result, reverse('ct:lesson', args=(course.id, self.unit.id, unit_lesson.id)))

        get_type.return_value = IS_LESSON
        result = unit_lesson.get_url(base_path, subpath='faq')
        self.assertEqual(result, reverse('ct:ul_faq_student', args=(course.id, self.unit.id, unit_lesson.id)))

        result = unit_lesson.get_url(base_path, subpath='')
        self.assertEqual(result, reverse('ct:lesson', args=(course.id, self.unit.id, unit_lesson.id)))

    def test_get_type(self):
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42, lesson=self.lesson)
        unit_lesson.lesson.concept = self.concept

        unit_lesson.kind = UnitLesson.MISUNDERSTANDS
        self.assertEqual(unit_lesson.get_type(), IS_ERROR)

        unit_lesson.kind = UnitLesson.RESOLVES
        self.assertEqual(unit_lesson.get_type(), IS_CONCEPT)

        unit_lesson.lesson.concept = None
        self.assertEqual(unit_lesson.get_type(), IS_LESSON)

    @patch('ct.models.reverse')
    def test_get_study_url(self, reverse):
        course = Course(title='test_title', addedBy=self.user)
        course.save()
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42, lesson=self.lesson)
        unit_lesson.save()
        unit_lesson.get_study_url(course.id)
        reverse.assert_called_once_with('ct:ul_respond', args=(course.id, self.unit.pk, unit_lesson.pk))

        reverse.reset_mock()

        self.lesson.kind = Lesson.EXERCISE
        unit_lesson.get_study_url(course.id)
        reverse.assert_called_once_with('ct:lesson', args=(course.id, self.unit.pk, unit_lesson.pk))

    def test_is_question(self):
        unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42, lesson=self.lesson)
        self.assertTrue(unit_lesson.is_question())

        self.lesson.kind = Lesson.EXERCISE
        self.assertFalse(unit_lesson.is_question())
