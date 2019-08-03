from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0003_auto_20141110_2153'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('response', models.ForeignKey(to='ct.Response', on_delete=models.CASCADE)),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InquiryCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('response', models.ForeignKey(to='ct.Response', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Liked',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='concept',
            name='description',
        ),
        migrations.AddField(
            model_name='lesson',
            name='concept',
            field=models.ForeignKey(to='ct.Concept', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='conceptlink',
            name='relationship',
            field=models.CharField(default='defines', max_length=10, choices=[('defines', 'Defines'), ('tests', 'Tests understanding of'), ('resol', 'Helps students resolve'), ('derives', 'Derives'), ('proves', 'Proves'), ('assumes', 'Assumes'), ('motiv', 'Motivates'), ('illust', 'Illustrates'), ('intro', 'Introduces'), ('comment', 'Comments on'), ('warns', 'Warns about')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='course',
            field=models.ForeignKey(to='ct.Course', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='response',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='studenterror',
            name='errorModel',
            field=models.ForeignKey(to='ct.UnitLesson', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='unitlesson',
            name='kind',
            field=models.CharField(default='part', max_length=10, choices=[('part', 'Included in this courselet'), ('answers', 'Answer for a question'), ('errmod', 'Common error for a question'), ('resol', 'Resolution for an error'), ('pretest', 'Pre-test/Post-test for this courselet'), ('subunit', 'Container for this courselet')]),
        ),
    ]
