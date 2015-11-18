import urllib

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ct.models import Unit, Concept, Lesson, UnitLesson, Course, CourseUnit, Role
from ct.tests.integrate import OurTestCase


class FunctionTests(OurTestCase):
    def setUp(self):
            self.user = User.objects.create_user(
                username='jacob', email='jacob@_', password='top_secret'
            )
            self.client.login(username='jacob', password='top_secret')
            self.wikiUser = User.objects.create_user(
                username='wikipedia', email='wiki@_', password='top_secret'
            )
            self.unit = Unit(title='My Courselet', addedBy=self.user)
            self.unit.save()

    def test_sourceDB(self):
        """
        Check wikipedia concept retrieval.
        """
        c, lesson = Concept.get_from_sourceDB('New York City', self.user)
        self.assertEqual(c.title, 'New York City')
        self.assertEqual(c.addedBy, self.user)
        self.assertEqual(lesson.addedBy, self.wikiUser)
        self.assertEqual(lesson.concept, c)
        self.assertTrue(lesson.is_committed())
        self.assertEqual(lesson.changeLog, 'initial text from wikipedia')
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertEqual(lesson.sourceID, 'New York City')
        self.assertIn('City of New York', lesson.text)
        # check that subsequent retrieval uses stored db record
        c2, l2 = Concept.get_from_sourceDB('New York City', self.user)
        self.assertEqual(c2.pk, c.pk)
        self.assertEqual(l2.pk, lesson.pk)
        self.assertIn(c, list(Concept.search_text('new york')))

    def test_sourceDB_temp(self):
        """
        Check wikipedia temporary document retrieval.
        """
        lesson = Lesson.get_from_sourceDB(
            'New York City', self.user, doSave=False
        )
        self.assertIn('City of New York', lesson.text)  # got the text?
        self.assertEqual(Lesson.objects.count(), 0)  # nothing saved?

    def test_wikipedia_view(self):
        """
        Check wikipedia view and concept addition method.
        """
        url = '/ct/teach/courses/1/units/%d/concepts/wikipedia/%s/' % (self.unit.pk, urllib.quote('New York City'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'City of New York')
        self.check_post_get(url, dict(task='add'), '/', 'City of New York')
        ul = UnitLesson.objects.get(
            lesson__concept__title='New York City', unit=self.unit
        )  # check UL & concept added
        self.assertTrue(ul in UnitLesson.search_sourceDB('New York City')[0])
        self.assertTrue(ul in UnitLesson.search_sourceDB('New York City', unit=self.unit)[0])


class LessonFunctionalMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')

    def test_search_sourceDB(self):
        'check wikipedia search'
        results = Lesson.search_sourceDB('new york city')
        self.assertTrue(len(results) >= 10)
        self.assertIn('New York City', [t[0] for t in results])
        self.assertEqual(len(results[0]), 3)

    def test_get_from_sourceDB_noSave_wiki_user(self):
        user = User.objects.create_user(username='wikipedia', password='wiki')
        lesson = Lesson.get_from_sourceDB('New York', user, doSave=False)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, user)
        self.assertEqual(lesson.title, 'New York')
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertFalse(Lesson.objects.filter(addedBy=self.user).exists())

    def test_get_from_sourceDB(self):
        lesson = Lesson.get_from_sourceDB('New York', self.user)
        self.assertIsInstance(lesson, Lesson)
        self.assertEqual(lesson.addedBy, self.user)
        self.assertEqual(lesson.title, 'New York')
        self.assertEqual(lesson.sourceDB, 'wikipedia')
        self.assertIsNotNone(lesson.commitTime)
        self.assertTrue(Lesson.objects.filter(addedBy=self.user).exists())


class ConceptsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='New York Test Lesson', text='brr', addedBy=self.user)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()

    def test_unit_concepts_search(self):
        self.lesson.concept = self.concept
        self.lesson.save()
        response = self.client.get(
            reverse('ct:unit_concepts', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}),
            {'search': 'New York'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/concepts.html')
        self.assertIn('actionTarget', response.context)
        cset_dict = {i[0]: i[1] for i in response.context['cset']}
        self.assertIn('New York Test Lesson', cset_dict)
        self.assertIn('New York', cset_dict)
        self.assertIn('The New York Times Company', cset_dict)
