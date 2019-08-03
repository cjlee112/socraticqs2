from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0010_auto_20150129_1209'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nodeName', models.CharField(max_length=64)),
                ('startTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time created')),
                ('endTime', models.DateTimeField(null=True, verbose_name='time ended')),
                ('exitEvent', models.CharField(max_length=64)),
                ('activity', models.ForeignKey(to='ct.ActivityLog', on_delete=models.CASCADE)),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='activityEvent',
            field=models.ForeignKey(to='ct.ActivityEvent', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
