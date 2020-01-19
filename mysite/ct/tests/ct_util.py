"""
Unit tests for ct/ct_util.py.
"""
from django.test import TestCase

from ddt import ddt, data, unpack
from unittest.mock import Mock

from ct.ct_util import get_path_kwargs, reverse_path_args, get_middle_indexes


@ddt
class GetPathKwargsTest(TestCase):
    """
    Tests for get_path_kwargs helper function.
    """
    @data('/ct/courses/1/units/1/', '/ct/courses/1/units/1/error_pathKwargs/1/')
    def test_get_path_kwargs(self, path):
        """Return args from path with id's.

        Function should return dict with arg and id.
        If arg is incorrect - ignore it.
        """
        result = get_path_kwargs(path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'course_id': 1, 'unit_id': 1})


class ReversePathArgsTest(TestCase):
    """
    Tests for reverse_path_args helper func.
    """
    def test_reverse_path_args(self):
        """
        Helper to return path based on target url by namespace and/or args.
        """
        result = reverse_path_args('ct:ul_teach', '/ct/teach/courses/21/units/33/', ul_id=2)
        self.assertEqual(result, '/ct/teach/courses/21/units/33/lessons/2/')

        unit_lesson_object = Mock()
        unit_lesson_object.pk = 2
        result = reverse_path_args('ct:ul_teach', '/ct/teach/courses/21/units/33/', unitLesson=unit_lesson_object)
        self.assertEqual(result, '/ct/teach/courses/21/units/33/lessons/2/')


@ddt
class AuxiliariesTest(TestCase):
    """
    Tests various auxiliary functions.
    """

    @data(
        ([1], [None]),
        ([1, 2], [None]),
        ([1, 2, 3], [1]),
        ([1, 2, 3, 4], [1, 2])
    )
    @unpack
    def test_get_middle_indexes(self, input_value, output_value):
        """
        Ensure proper middle indexes are returned.
        """
        output = get_middle_indexes(input_value)
        self.assertEqual(output, output_value)
