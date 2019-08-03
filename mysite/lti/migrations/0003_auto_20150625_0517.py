from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0014_fsmgroup'),
        ('lti', '0002_auto_20150429_0310'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseRef',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Creation date and time')),
                ('context_id', models.CharField(max_length=254, verbose_name='LTI context_id')),
                ('tc_guid', models.CharField(max_length=128, verbose_name='LTI tool_consumer_instance_guid')),
                ('course', models.ForeignKey(verbose_name='Courslet Course', to='ct.Course', on_delete=models.CASCADE)),
                ('instructors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Course Instructors')),
            ],
            options={
                'verbose_name': 'CourseRef',
                'verbose_name_plural': 'CourseRefs',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='courseref',
            unique_together=set([('context_id', 'course')]),
        ),
        migrations.AlterField(
            model_name='ltiuser',
            name='course_id',
            field=models.CharField(max_length=255),
            preserve_default=True,
        ),
    ]
