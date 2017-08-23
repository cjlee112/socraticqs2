# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0029_auto_20170525_0116'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interestedform',
            name='when_join',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='description_field',
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='btn_text',
            field=models.CharField(default=b'Schedule to demo', max_length=70),
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='email_to',
            field=models.EmailField(default=b'dummy@mail.com', max_length=254),
        ),
    ]
