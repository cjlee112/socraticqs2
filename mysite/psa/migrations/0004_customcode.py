# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default', '0003_alter_email_max_length'),
        ('psa', '0003_auto_20150420_0308'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomCode',
            fields=[
                ('code_ptr', models.OneToOneField(
                    parent_link=True, auto_created=True, primary_key=True,
                    serialize=False, to='default.Code')),
                ('user_id', models.IntegerField(null=True)),
            ],
            options={
            },
            bases=('default.code',),
        ),
    ]
