# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0013_response_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='FSMGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.CharField(max_length=64)),
                ('fsm', models.ForeignKey(to='ct.FSM')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
