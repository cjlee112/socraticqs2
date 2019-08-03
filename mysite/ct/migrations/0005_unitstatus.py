from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0004_auto_20141117_2208'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('startTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time started')),
                ('endTime', models.DateTimeField(null=True, verbose_name='time ended')),
                ('order', models.IntegerField(default=0)),
                ('unit', models.ForeignKey(to='ct.Unit', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
