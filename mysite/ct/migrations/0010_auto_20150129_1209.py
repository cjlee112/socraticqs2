from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0009_auto_20150127_1752'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activityevent',
            name='activity',
        ),
        migrations.RemoveField(
            model_name='activityevent',
            name='unitLesson',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='activityEvent',
        ),
        migrations.DeleteModel(
            name='ActivityEvent',
        ),
    ]
