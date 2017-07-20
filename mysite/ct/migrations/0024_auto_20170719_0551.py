# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0023_course_copied_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=50, null=True, choices=[(b'choices', b'Multiple Choices Question')]),
        ),
        migrations.AddField(
            model_name='response',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'choices', b'Multiple Choices response')]),
        ),
    ]
