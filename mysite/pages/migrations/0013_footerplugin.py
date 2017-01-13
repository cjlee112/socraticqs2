# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0012_benefitsitemplugin_benefitsplugin'),
    ]

    operations = [
        migrations.CreateModel(
            name='FooterPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('footer_text', models.CharField(max_length=100, blank=True)),
                ('footer_link', models.CharField(max_length=200, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
