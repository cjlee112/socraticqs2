from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0024_auto_20151106_1545'),
    ]

    operations = [
        migrations.CreateModel(
            name='SlideShareItemPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE)),
                ('hidden', models.BooleanField(default=False)),
                ('slideshare_code', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='SlideSharePlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE)),
                ('hidden', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=200)),
                ('description', djangocms_text_ckeditor.fields.HTMLField()),
                ('background', models.CharField(default='grey', max_length=70, choices=[('gray', 'section-2-cols-bg'), ('none', '')])),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.RenameField(
            model_name='interestedform',
            old_name='first_name',
            new_name='role',
        ),
        migrations.RemoveField(
            model_name='interestedform',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='interestedform',
            name='timezone',
        ),
        migrations.RemoveField(
            model_name='interestedform',
            name='when_join',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='description_field',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='first_name_error_msg',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='last_name_error_msg',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='timezone_error_msg',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='timezone_field',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='when_error_msg',
        ),
        migrations.RemoveField(
            model_name='interestedplugin',
            name='when_field',
        ),
        migrations.AddField(
            model_name='interestedform',
            name='name',
            field=models.CharField(max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedform',
            name='organization',
            field=models.CharField(max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='name_error_msg',
            field=models.CharField(default='Please enter your name', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='organization_error_msg',
            field=models.CharField(default='Please enter your Institute/Organization', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='organization_field',
            field=models.CharField(default='Institution/Organization', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='role_error_msg',
            field=models.CharField(default='Please enter your Title/Role', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='role_field',
            field=models.CharField(default=' Title/Role', max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='description',
            field=models.TextField(default='Get on our mailing list and we\xe2\x80\x99ll contact you about the next hackathon.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='title',
            field=models.CharField(default='I\xe2\x80\x99m Interested in the hackathon', max_length=200),
            preserve_default=True,
        ),
    ]
