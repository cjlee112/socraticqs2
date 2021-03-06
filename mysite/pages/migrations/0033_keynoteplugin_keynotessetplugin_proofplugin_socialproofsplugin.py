from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djangocms_text_ckeditor.fields
import filer.fields.image


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0020_old_tree_cleanup'),
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        ('pages', '0032_auto_20181114_1351'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyNotePlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_keynoteplugin', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('button_text', models.CharField(blank=True, max_length=200)),
                ('uid', models.SlugField(max_length=8, unique=True)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', djangocms_text_ckeditor.fields.HTMLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='KeyNotesSetPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_keynotessetplugin', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', djangocms_text_ckeditor.fields.HTMLField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='ProofPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_proofplugin', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', djangocms_text_ckeditor.fields.HTMLField()),
                ('proof_icon', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proof_icon', to=settings.FILER_IMAGE_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='SocialProofsPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_socialproofsplugin', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('post_description', djangocms_text_ckeditor.fields.HTMLField()),
                ('more_proofs_link', models.URLField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
