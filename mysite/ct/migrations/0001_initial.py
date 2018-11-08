# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('isError', models.BooleanField(default=False)),
                ('isAbort', models.BooleanField(default=False)),
                ('isFail', models.BooleanField(default=False)),
                ('isPuzzled', models.BooleanField(default=False)),
                ('alwaysAsk', models.BooleanField(default=False)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('approvedBy', models.ForeignKey(related_name=b'approvedConcepts', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptGraph',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'depends', max_length=10, choices=[(b'depends', b'Depends on'), (b'motiv', b'Motivates'), (b'errmod', b'misunderstands'), (b'violates', b'Violates'), (b'contains', b'Contains'), (b'tests', b'Tests'), (b'conflicts', b'Conflicts with'), (b'proves', b'Proves'), (b'dispro', b'Disproves')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('approvedBy', models.ForeignKey(related_name=b'approvedConceptEdges', to=settings.AUTH_USER_MODEL, null=True)),
                ('fromConcept', models.ForeignKey(related_name=b'relatedTo', to='ct.Concept')),
                ('toConcept', models.ForeignKey(related_name=b'relatedFrom', to='ct.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'defines', max_length=10, choices=[(b'is', b'Represents (unique ID)'), (b'defines', b'Defines'), (b'informal', b'Intuitive statement of'), (b'formaldef', b'Formal definition for'), (b'derives', b'Derives'), (b'proves', b'Proves'), (b'assumes', b'Assumes'), (b'motiv', b'Motivates'), (b'illust', b'Illustrates'), (b'intro', b'Introduces'), (b'comment', b'Comments on'), (b'warns', b'Warning about')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concept', models.ForeignKey(to='ct.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('access', models.CharField(default=b'public', max_length=10, choices=[(b'public', b'Public'), (b'enroll', b'By instructors only'), (b'private', b'By author only')])),
                ('enrollCode', models.CharField(max_length=64, null=True)),
                ('lockout', models.CharField(max_length=200, null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(to='ct.Course')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMEdge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('funcName', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('data', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('path', models.CharField(max_length=200)),
                ('data', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('fsm', models.ForeignKey(to='ct.FSM')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.TextField(null=True)),
                ('isModal', models.BooleanField(default=False)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time started')),
                ('fsmNode', models.ForeignKey(to='ct.FSMNode')),
                ('linkState', models.ForeignKey(related_name=b'linkChildren', to='ct.FSMState', null=True)),
                ('parentState', models.ForeignKey(related_name=b'children', to='ct.FSMState', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('text', models.TextField(null=True)),
                ('data', models.TextField(null=True)),
                ('url', models.CharField(max_length=256, null=True)),
                ('kind', models.CharField(default=b'base', max_length=10, choices=[(b'base', b'brief definition and explanation'), (b'explanation', b'long explanation'), (b'orct', b'Open Response Concept Test question'), (b'mcct', b'Concept Inventory Test question'), (b'exercise', b'exercise'), (b'project', b'project'), (b'practice', b'practice exam question'), (b'answer', b'answer'), (b'errmod', b'error model'), (b'data', b'data'), (b'case', b'Case Study'), (b'e-pedia', b'Encyclopedia'), (b'faq', b'frequently asked question'), (b'forum', b'forum')])),
                ('medium', models.CharField(default=b'reading', max_length=10, choices=[(b'reading', b'reading'), (b'lecture', b'lecture'), (b'slides', b'slides'), (b'video', b'video'), (b'audio', b'audio'), (b'image', b'image'), (b'db', b'Database'), (b'software', b'software')])),
                ('access', models.CharField(default=b'public', max_length=10, choices=[(b'public', b'Public'), (b'enroll', b'By instructors only'), (b'exam', b'Protected exam only'), (b'private', b'By author only')])),
                ('sourceDB', models.CharField(max_length=32, null=True)),
                ('sourceID', models.CharField(max_length=100, null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('treeID', models.IntegerField(null=True)),
                ('changeLog', models.TextField(null=True)),
                ('commitTime', models.DateTimeField(null=True, verbose_name=b'time committed')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('mergeParent', models.ForeignKey(related_name=b'mergeChildren', to='ct.Lesson', null=True)),
                ('parent', models.ForeignKey(related_name=b'children', to='ct.Lesson', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default=b'orct', max_length=10, choices=[(b'orct', b'ORCT response'), (b'sq', b'Question about a lesson'), (b'comment', b'Reply comment')])),
                ('text', models.TextField()),
                ('confidence', models.CharField(max_length=10, choices=[(b'guess', b'Just guessing'), (b'notsure', b'Not quite sure'), (b'sure', b'Pretty sure')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('selfeval', models.CharField(max_length=10, null=True, choices=[(b'different', b'Different'), (b'close', b'Close'), (b'correct', b'Essentially the same')])),
                ('status', models.CharField(max_length=10, null=True, choices=[(b'help', b'Still confused, need help'), (b'review', b'OK, but flag this for me to review'), (b'done', b'Solidly')])),
                ('needsEval', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(to='ct.Course', null=True)),
                ('lesson', models.ForeignKey(to='ct.Lesson')),
                ('parent', models.ForeignKey(to='ct.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(default=b'student', max_length=10, choices=[(b'prof', b'Instructor'), (b'TA', b'Teaching Assistant'), (b'student', b'Enrolled Student'), (b'self', b'Self-study')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('course', models.ForeignKey(to='ct.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudentError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('status', models.CharField(max_length=10, null=True, choices=[(b'help', b'Still confused, need help'), (b'review', b'OK, but flag this for me to review'), (b'done', b'Solidly')])),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lesson', models.ForeignKey(to='ct.Lesson')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('kind', models.CharField(default=b'unit', max_length=10, choices=[(b'unit', b'Courselet'), (b'live', b'Live session'), (b'resol', b'Resolutions for an error model')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time created')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default=b'part', max_length=10, choices=[(b'part', b'Included in this courselet'), (b'answers', b'Answer for a question'), (b'errmod', b'Common error for a question'), (b'pretest', b'Pre-test/Post-test for this courselet'), (b'subunit', b'Container for this courselet')])),
                ('order', models.IntegerField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time added')),
                ('treeID', models.IntegerField()),
                ('branch', models.CharField(default=b'master', max_length=32)),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('lesson', models.ForeignKey(to='ct.Lesson', null=True)),
                ('parent', models.ForeignKey(to='ct.UnitLesson', null=True)),
                ('unit', models.ForeignKey(to='ct.Unit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='studenterror',
            name='errorModel',
            field=models.ForeignKey(blank=True, to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studenterror',
            name='response',
            field=models.ForeignKey(to='ct.Response'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='fromNode',
            field=models.ForeignKey(related_name=b'outgoing', to='ct.FSMNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='toNode',
            field=models.ForeignKey(related_name=b'incoming', to='ct.FSMNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsm',
            name='startNode',
            field=models.ForeignKey(related_name=b'+', to='ct.FSMNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courseunit',
            name='unit',
            field=models.ForeignKey(to='ct.Unit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conceptlink',
            name='lesson',
            field=models.ForeignKey(to='ct.Lesson'),
            preserve_default=True,
        ),
    ]
