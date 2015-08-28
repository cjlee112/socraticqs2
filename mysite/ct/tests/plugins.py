from django.test import TestCase
from mock import Mock, patch

from ct.sourcedb_plugin.wikipedia_plugin import LessonDoc


@patch('ct.sourcedb_plugin.wikipedia_plugin.wikipedia')
class LessonDocTest(TestCase):
    """
    Tests for wikipedia plugin.
    """
    def test_init(self, wikipedia):
        sourceID = Mock()
        _data = Mock()
        wikipedia.page.return_value = _data
        lesson_doc = LessonDoc(sourceID=sourceID)
        wikipedia.page.assert_called_once_with(sourceID)
        self.assertIsInstance(lesson_doc, LessonDoc)
        self.assertEqual(lesson_doc._data, _data)
        self.assertEqual(lesson_doc.sourceID, sourceID)
        self.assertEqual(lesson_doc.title, sourceID)
        self.assertEqual(lesson_doc.description, _data.summary)
        self.assertEqual(lesson_doc.url, _data.url)

    def test_search(self, wikipedia):
        wikipedia.search.return_value = 'test_result1 test_result2'
        sourceID = Mock()
        max_results = Mock()
        result = LessonDoc.search(sourceID, max_results=max_results)
        wikipedia.search.assert_called_once_with(sourceID, max_results)
        self.assertIsInstance(result, list)
        self.assertEqual(
            result,
            [(s, s, 'http://en.wikipedia.org/wiki/' + '_'.join(s.split())) for s in wikipedia.search.return_value]
        )
