from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0018_unit_small_img_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concept',
            name='approvedBy',
            field=models.ForeignKey(related_name='approvedConcepts', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='conceptgraph',
            name='approvedBy',
            field=models.ForeignKey(related_name='approvedConceptEdges', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='course',
            name='enrollCode',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='course',
            name='lockout',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='courseunit',
            name='releaseTime',
            field=models.DateTimeField(null=True, verbose_name='time released', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='changeLog',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='commitTime',
            field=models.DateTimeField(null=True, verbose_name='time committed', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='concept',
            field=models.ForeignKey(blank=True, to='ct.Concept', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='data',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='mergeParent',
            field=models.ForeignKey(related_name='mergeChildren', blank=True, to='ct.Lesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='parent',
            field=models.ForeignKey(related_name='children', blank=True, to='ct.Lesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='sourceDB',
            field=models.CharField(max_length=32, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='sourceID',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='treeID',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='url',
            field=models.CharField(max_length=256, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='response',
            name='activity',
            field=models.ForeignKey(blank=True, to='fsm.ActivityLog', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='response',
            name='parent',
            field=models.ForeignKey(blank=True, to='ct.Response', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='response',
            name='title',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studenterror',
            name='activity',
            field=models.ForeignKey(blank=True, to='fsm.ActivityLog', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unitlesson',
            name='lesson',
            field=models.ForeignKey(blank=True, to='ct.Lesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unitlesson',
            name='order',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unitlesson',
            name='parent',
            field=models.ForeignKey(blank=True, to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
