from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0023_auto_20151106_1047'),
    ]

    operations = [
        migrations.RenameField(
            model_name='interestedform',
            old_name='description',
            new_name='when_join',
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='btn_text',
            field=models.CharField(default='Keep Me Informed', max_length=70),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='description',
            field=models.TextField(default=b"There is no commitment to take the workshop at this point. We'll contact you when we get enough participants to schedule a workshop."),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='email_error_msg',
            field=models.CharField(default='Please enter your email', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='email_to',
            field=models.EmailField(default='cmathews@elancecloud.com', max_length=75),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='first_name_error_msg',
            field=models.CharField(default='Please enter your first name', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='last_name_error_msg',
            field=models.CharField(default='Please enter your last name', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='timezone_error_msg',
            field=models.CharField(default='Please enter your timezone', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='title',
            field=models.CharField(default='I\xe2\x80\x99m Interested in the Online Workshop', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='when_error_msg',
            field=models.CharField(default='Please tell us when you can join', max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='description_field',
            field=djangocms_text_ckeditor.fields.HTMLField(default='We plan to host hackathons between ? and ?. Please tell us more about your availability below. Our hackathons are split into 3 meetings that are about 2 hours long.'),
            preserve_default=True,
        ),
    ]
