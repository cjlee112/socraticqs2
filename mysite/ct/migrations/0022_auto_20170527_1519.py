from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0021_lesson_add_unit_aborts'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='role',
            unique_together=set([('role', 'course', 'user')]),
        ),
    ]
