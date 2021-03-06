from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0020_old_tree_cleanup'),
        ('pages', '0035_helpcentermodel_intercomarticlemodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hero1Model',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_hero1model', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('best_prattices_text', models.CharField(max_length=200)),
                ('best_prattices_link', models.URLField()),
                ('bp1_text', models.CharField(max_length=200)),
                ('bp1_link', models.URLField()),
                ('video_url', models.URLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='Hero2Model',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_hero2model', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('best_prattices_text', models.CharField(max_length=200)),
                ('best_prattices_link', models.URLField()),
                ('bp2_text', models.CharField(max_length=200)),
                ('bp2_link', models.URLField()),
                ('video_url', models.URLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
