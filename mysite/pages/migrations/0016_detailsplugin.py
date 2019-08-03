from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0015_faqitemplugin_faqplugin'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetailsPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE)),
                ('title', models.CharField(max_length=70, blank=True)),
                ('video_url', models.URLField()),
                ('details_text', models.CharField(max_length=70)),
                ('quote_text', models.CharField(max_length=70)),
                ('quote_small', models.CharField(max_length=70)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
