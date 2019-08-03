from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0009_auto_20170525_0116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outcomeservice',
            name='lis_outcome_service_url',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='outcomeservice',
            unique_together=set([('lis_outcome_service_url', 'lti_consumer')]),
        ),
    ]
