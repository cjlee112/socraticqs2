from django.db import models, migrations
import lti.utils


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0007_auto_20170410_0552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_key',
            field=models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=64, db_index=True),
        ),
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_secret',
            field=models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=64),
        ),
    ]
