from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0028_auto_20181022_0142'),
        ('accounts', '0006_instructor_what_do_you_teach'),
        ('chat', '0014_auto_20181116_0657'),
        ('ctms', '0002_invite_enroll_unit_code'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('instructor', 'email', 'type', 'course', 'enroll_unit_code')]),
        ),
    ]
