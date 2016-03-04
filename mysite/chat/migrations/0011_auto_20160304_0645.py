# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('fsm', '0002_auto_20150723_0243'),
        ('chat', '0010_message_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.ForeignKey(to='ct.Response')),
                ('unit', models.ForeignKey(to='ct.Unit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='message',
            name='options',
        ),
        migrations.AddField(
            model_name='chat',
            name='fsm_state',
            field=models.ForeignKey(to='fsm.FSMState', null=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='message',
            name='input_type',
            field=models.CharField(max_length=16, null=True, choices=[(b'text', b'text'), (b'options', b'options'), (b'errors', b'errors'), (b'custom', b'custom')]),
            preserve_default=True,
        ),
    ]
