"""
Unit tests for core app forms.py.
"""

from django.test import TestCase

from ct.forms import *


class FormsTest(TestCase):
    """
    Tests for forms.
    """
    def test_response_form_positive(self):
        data = {'text': 'test answer', 'confidence': 'guess'}
        form = ResponseForm(data=data)
        self.assertTrue(form.is_valid())

    def test_response_form_negative(self):
        data = {'text': 'test answer', 'confidence': ''}
        form = ResponseForm(data=data)
        self.assertFalse(form.is_valid())

    def test_self_assess_form_positive(self):
        data = {'selfeval': 'correct', 'status': 'review'}
        form = SelfAssessForm(data=data)
        self.assertTrue(form.is_valid())

    def test_self_assess_form_negative(self):
        data = {'selfeval': 'correct', 'status': 'false_status'}
        form = SelfAssessForm(data=data)
        self.assertFalse(form.is_valid())

    def test_reorder_form_positive(self):
        data = {'newOrder': '0', 'oldOrder': '1'}
        form = ReorderForm(0, 2, data)
        self.assertTrue(form.is_valid())

    def test_reorder_form_negative(self):
        data = {'newOrder': 'false1', 'oldOrder': 'false2'}
        form = ReorderForm(0, 2, data)
        self.assertFalse(form.is_valid())

    def test_next_like_form_positive(self):
        form = NextLikeForm(data={'liked': 'on'})
        self.assertTrue(form.is_valid())

    def test_next_like_form_negative(self):
        form = NextLikeForm()
        self.assertFalse(form.is_valid())

    def test_next_form_positive(self):
        form = NextForm(data={'fsmtask': 'launch'})
        self.assertTrue(form.is_valid())

    def test_next_form_negative(self):
        form = NextForm(data={'fsmtask_false': 'launch'})
        self.assertFalse(form.is_valid())

    def test_unit_title_form_positive(self):
        form = UnitTitleForm(data={'title': 'test_title'})
        self.assertTrue(form.is_valid())

    def test_unit_title_form_negative(self):
        form = UnitTitleForm(data={'title_false': 'test_title'})
        self.assertFalse(form.is_valid())

    def test_course_title_form_positive(self):
        form = CourseTitleForm(data={'title': 'test_title', 'access': 'public', 'description': 'test_description'})
        self.assertTrue(form.is_valid())

    def test_course_title_form_negative(self):
        form = CourseTitleForm(data={'title': 'test_title'})
        self.assertFalse(form.is_valid())

    def test_concept_form_positive(self):
        form = ConceptForm(data={'title': 'test_title'})
        self.assertTrue(form.is_valid())

    def test_concept_form_negative(self):
        form = ConceptForm(data={'title_false': 'test_title'})
        self.assertFalse(form.is_valid())

    def test_new_concept_form_positive(self):
        form = NewConceptForm(data={'title': 'test_title', 'description': 'test_description', 'submitLabel': 'label'})
        self.assertTrue(form.is_valid())

    def test_new_concept_form_negative(self):
        form = NewConceptForm(data={'title': 'test_title'})
        self.assertFalse(form.is_valid())

    def test_concept_link_form_positive(self):
        form = ConceptLinkForm(data={'relationship': 'defines'})
        self.assertTrue(form.is_valid())

    def test_concept_link_form_negative(self):
        form = ConceptLinkForm(data={'relationship': 'false_rel'})
        self.assertFalse(form.is_valid())

    def test_concept_graph_form_positive(self):
        form = ConceptGraphForm(data={'relationship': 'depends'})
        self.assertTrue(form.is_valid())

    def test_concept_graph_form_negative(self):
        form = ConceptGraphForm(data={'relationship': 'false_rel'})
        self.assertFalse(form.is_valid())

    def test_new_error_form_positive(self):
        form = NewErrorForm(data={'title': 'test_title', 'text': 'test_text'})
        self.assertTrue(form.is_valid())

    def test_new_error_form_negative(self):
        form = NewErrorForm(data={'title_false': 'test_title', 'text': 'test_text'})
        self.assertFalse(form.is_valid())

    def test_search_form_positive(self):
        """
        Base Form.
        """
        form = SearchFormBase(data={})
        self.assertTrue(form.is_valid())

    def test_logout_form(self):
        form = LogoutForm(data={'task': 'task_name'})
        self.assertTrue(form.is_valid())

    def test_cancel_form(self):
        form = CancelForm(data={'task': 'task_name'})
        self.assertTrue(form.is_valid())
