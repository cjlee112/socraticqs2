from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0020_old_tree_cleanup'),
        ('pages', '0034_auto_20190611_0449'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelpCenterModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_helpcentermodel', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('link_text', models.CharField(max_length=200)),
                ('link_url', models.URLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='IntercomArticleModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_intercomarticlemodel', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('short_description', models.TextField(blank=True)),
                ('link_text', models.CharField(max_length=200)),
                ('link_url', models.URLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
