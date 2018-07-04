# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0023_course_copied_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='attachment',
            field=models.FileField(null=True, upload_to=b'questions', blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='enable_auto_grading',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_max_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_min_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=50, null=True, choices=[(b'choices', b'Multiple Choices Question'), (b'numbers', b'Numbers'), (b'equation', b'Equation'), (b'canvas', b'Canvas')]),
        ),
        migrations.AddField(
            model_name='response',
            name='attachment',
            field=models.FileField(null=True, upload_to=b'answers', blank=True),
        ),
        migrations.AddField(
            model_name='response',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='response',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'choices', b'Multiple Choices response'), (b'numbers', b'Numbers response'), (b'equation', b'Equation response'), (b'canvas', b'Canvas response')]),
        ),
        migrations.AlterField(
            model_name='course',
            name='title',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^\\s+?$', message=b'This field can not consist of only spaces', inverse_match=True)]),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='title',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^\\s+?$', message=b'This field can not consist of only spaces', inverse_match=True)]),
        ),
        migrations.AlterField(
            model_name='unit',
            name='title',
            field=models.CharField(help_text=b'Your students will see this, so give your courselet a descriptive name.', max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^\\s+?$', message=b'This field can not consist of only spaces', inverse_match=True)]),
        ),
    ]
