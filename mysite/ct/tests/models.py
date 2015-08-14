"""
Unit tests for core app models.py.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mock import Mock, patch

from ct.models import *


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
