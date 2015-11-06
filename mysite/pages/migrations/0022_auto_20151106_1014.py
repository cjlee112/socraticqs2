# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0021_interestedplugin_email_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='interestedplugin',
            name='description',
            field=models.TextField(default=b"There is no commitment to take the workshop at this point. We'll contact you when we get enough participants to schedule a workshop."),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='email_error_msg',
            field=models.CharField(default=b'Please enter your email', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='first_name_error_msg',
            field=models.CharField(default=b'Please enter your first name', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='last_name_error_msg',
            field=models.CharField(default=b'Please enter your last name', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='timezone_error_msg',
            field=models.CharField(default=b'Please enter your timezone', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='title',
            field=models.CharField(default=b'I\xe2\x80\x99m Interested in the Online Workshop', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='when_error_msg',
            field=models.CharField(default=b'Please tell us when you can join', max_length=200),
            preserve_default=True,
        ),
    ]
