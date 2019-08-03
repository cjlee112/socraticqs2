from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0016_detailsplugin'),
    ]

    operations = [
        migrations.CreateModel(
            name='MiscItemPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE)),
                ('title', models.CharField(max_length=70, blank=True)),
                ('description_header', djangocms_text_ckeditor.fields.HTMLField(blank=True)),
                ('list_type', models.CharField(default='list-checklist', max_length=20, choices=[('list-questions', 'list-questions'), ('list_numeric', 'list_numeric'), ('list-checklist', 'list-checklist'), ('list-header', 'list-header')])),
                ('list_text', djangocms_text_ckeditor.fields.HTMLField()),
                ('description_footer', djangocms_text_ckeditor.fields.HTMLField(blank=True)),
                ('header_type_text', models.CharField(max_length=70, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.RemoveField(
            model_name='listplugin',
            name='description_footer',
        ),
        migrations.RemoveField(
            model_name='listplugin',
            name='description_header',
        ),
        migrations.AlterField(
            model_name='listplugin',
            name='list_type',
            field=models.CharField(default='list-questions', max_length=20, choices=[('list-questions', 'list-questions'), ('list_numeric', 'list_numeric'), ('list-checklist', 'list-checklist'), ('list-header', 'list-header')]),
            preserve_default=True,
        ),
    ]
