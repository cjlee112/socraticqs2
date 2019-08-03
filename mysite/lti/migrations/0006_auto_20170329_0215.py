from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lti', '0005_auto_20160224_0306'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradedLaunch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', models.IntegerField(db_index=True)),
                ('lis_result_sourcedid', models.CharField(max_length=255, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='OutcomeService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lis_outcome_service_url', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='gradedlaunch',
            name='outcome_service',
            field=models.ForeignKey(to='lti.OutcomeService', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='gradedlaunch',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='gradedlaunch',
            unique_together=set([('outcome_service', 'lis_result_sourcedid')]),
        ),
    ]
