# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('default', '0001_initial'),
        ('psa', '0002_usersession'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecondaryEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, verbose_name=b'Secondary Email')),
                ('provider', models.ForeignKey(to='default.UserSocialAuth')),
                ('user', models.ForeignKey(related_name='secondary', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='secondaryemail',
            unique_together=set([('provider', 'email')]),
        ),
    ]
