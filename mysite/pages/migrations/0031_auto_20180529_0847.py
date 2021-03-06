from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0030_auto_20170810_0212'),
    ]

    operations = [
        migrations.CreateModel(
            name='BecomeInstructorPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='pages_becomeinstructorplugin', serialize=False, to='cms.CMSPlugin')),
                ('hidden', models.BooleanField(default=False)),
                ('error_name', models.CharField(blank=True, max_length=200)),
                ('agreement_text', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        )
    ]
