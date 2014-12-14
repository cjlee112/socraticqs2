"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from ct.models import *

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
