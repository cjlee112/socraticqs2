from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0005_unitstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseunit',
            name='releaseTime',
            field=models.DateTimeField(null=True, verbose_name='time released'),
            preserve_default=True,
        ),
    ]
