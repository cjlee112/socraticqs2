from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0003_auto_20150625_0517'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ltiuser',
            old_name='course_id',
            new_name='context_id',
        ),
        migrations.AlterUniqueTogether(
            name='ltiuser',
            unique_together=set([('user_id', 'consumer', 'context_id')]),
        ),
    ]
