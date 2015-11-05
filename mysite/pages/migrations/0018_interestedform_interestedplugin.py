# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0017_auto_20151105_0807'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterestedForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=100, blank=True)),
                ('last_name', models.CharField(max_length=100, blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('description', models.TextField(blank=True)),
                ('timezone', models.CharField(max_length=70, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterestedPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('name_field', models.CharField(default=b'Name', max_length=200)),
                ('email_field', models.CharField(default=b'Email', max_length=200)),
                ('when_field', models.CharField(default=b'When can you join?', max_length=200)),
                ('description_field', djangocms_text_ckeditor.fields.HTMLField(default=b'We plan to host hackathons between ? and ?. Please tell us more about your availability below.Our hackathons are split into 3 meetings that are about 2 hours long.')),
                ('timezone_field', models.CharField(default=b' What is your timezone?', max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
