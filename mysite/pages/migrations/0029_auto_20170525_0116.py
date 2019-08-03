from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0028_auto_20151207_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interestedform',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='interestedplugin',
            name='email_to',
            field=models.EmailField(default='cmathews@elancecloud.com', max_length=254),
        ),
    ]
