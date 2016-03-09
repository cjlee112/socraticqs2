# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0012_auto_20160307_0359'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatDivider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='message',
            name='contenttype',
            field=models.CharField(default=b'NoneType', max_length=16, null=True, choices=[(b'NoneType', b'NoneType'), (b'chatdivider', b'chatdivider'), (b'response', b'response'), (b'unitlesson', b'unitlesson'), (b'uniterror', b'uniterror')]),
            preserve_default=True,
        ),
    ]
