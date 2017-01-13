# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0007_activelearningratesplugin'),
    ]

    operations = [
        migrations.CreateModel(
            name='ListPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('title', models.CharField(max_length=70, blank=True)),
                ('description_header', djangocms_text_ckeditor.fields.HTMLField(blank=True)),
                ('list_type', models.CharField(default=b'list-questions', max_length=20, choices=[(b'list-questions', b'list-questions')])),
                ('list_text', djangocms_text_ckeditor.fields.HTMLField()),
                ('description_footer', djangocms_text_ckeditor.fields.HTMLField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
