from django.test import TestCase
from mock import Mock, patch

from ct.sourcedb_plugin.wikipedia_plugin import LessonDoc
import wikipedia


@patch('ct.sourcedb_plugin.wikipedia_plugin.wikipedia')
class LessonDocTest(TestCase):
    """
    Tests for wikipedia plugin.
    """
    def test_init(self, wiki_mocked):
        sourceID = Mock()
        _data = Mock()
        wiki_mocked.page.return_value = _data
        lesson_doc = LessonDoc(sourceID=sourceID)
        wiki_mocked.page.assert_called_once_with(sourceID)
        self.assertIsInstance(lesson_doc, LessonDoc)
        self.assertEqual(lesson_doc._data, _data)
        self.assertEqual(lesson_doc.sourceID, sourceID)
        self.assertEqual(lesson_doc.title, sourceID)
        self.assertEqual(lesson_doc.description, _data.summary)
        self.assertEqual(lesson_doc.url, _data.url)

    def test_search(self, wiki_mocked):
        wiki_mocked.search.return_value = 'test_result1 test_result2'
        sourceID = Mock()
        max_results = Mock()
        result = LessonDoc.search(sourceID, max_results=max_results)
        wiki_mocked.search.assert_called_once_with(sourceID, max_results)
        self.assertIsInstance(result, list)
        self.assertEqual(
            result,
            [(s, s, 'http://en.wikipedia.org/wiki/' + '_'.join(s.split())) for s in wiki_mocked.search.return_value]
        )

    def for_future_init_wiki_exception(self, wiki_mocked):
        """Test case when wikipedia throw exception.

        Can't run test due to exception catching in LessonDoc.
        Need to change``except wikipedia.exceptions.DisambiguationError``
        to ``except DisambiguationError``
        """
        sourceID = Mock()
        wiki_mocked.page.side_effect = wikipedia.exceptions.PageError('test error')
        with self.assertRaises(KeyError):
            LessonDoc(sourceID=sourceID)
