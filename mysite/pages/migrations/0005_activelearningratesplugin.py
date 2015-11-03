# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filer.fields.image
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('filer', '0002_auto_20150606_2003'),
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0004_auto_20151021_0157'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveLearningRatesPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('title', models.CharField(max_length=70, blank=True)),
                ('description', djangocms_text_ckeditor.fields.HTMLField(blank=True)),
                ('image', filer.fields.image.FilerImageField(related_name='Active learning image', blank=True, to='filer.Image', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
