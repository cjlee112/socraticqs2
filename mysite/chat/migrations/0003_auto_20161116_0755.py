from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_chat_is_live'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollunitcode',
            name='isLive',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='enrollunitcode',
            unique_together=set([('enrollCode', 'courseUnit', 'isLive')]),
        ),
    ]
