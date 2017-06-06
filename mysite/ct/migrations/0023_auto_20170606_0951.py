# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0022_auto_20170601_0440'),
    ]

    operations = [
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
