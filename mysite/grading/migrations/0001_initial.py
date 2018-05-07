# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0025_auto_20180402_0432'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectnessMeter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('correctness', models.CharField(max_length=25, choices=[(b'correct', b'Correct'), (b'partially_correct', b'Partially correct'), (b'not_correct', b'Not correct')])),
                ('points', models.FloatField(default=0)),
                ('response', models.ForeignKey(to='ct.Response')),
            ],
        ),
    ]
