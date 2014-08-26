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
            name='CommonError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('synopsis', models.TextField()),
                ('disproof', models.TextField(null=True)),
                ('prescription', models.TextField(null=True)),
                ('dangerzone', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptEquation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('terms', models.CharField(max_length=200)),
                ('math', models.TextField()),
                ('explanation', models.TextField()),
                ('atime', models.DateTimeField(verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'depends', max_length=10, choices=[(b'depends', b'Depends on'), (b'motiv', b'Motivates')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('fromConcept', models.ForeignKey(related_name=b'relatedTo', to='ct.Concept')),
                ('toConcept', models.ForeignKey(related_name=b'relatedFrom', to='ct.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptPicture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('terms', models.CharField(max_length=200)),
                ('explanation', models.TextField()),
                ('atime', models.DateTimeField(verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default=b'term', max_length=10, choices=[(b'term', b'Vocabulary Term'), (b'pict', b'Picture'), (b'eq', b'Equation')])),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concept', models.ForeignKey(to='ct.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CounterExample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('intro', models.TextField()),
                ('hint', models.TextField()),
                ('conclusion', models.TextField()),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('commonError', models.ForeignKey(to='ct.CommonError')),
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
                ('access', models.CharField(default=b'public', max_length=10, choices=[(b'public', b'Public'), (b'instr', b'By instructors only'), (b'private', b'By author only')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseErrorModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(to='ct.Course')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True)),
                ('intro', models.TextField(null=True)),
                ('conclusion', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Courselet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concepts', models.ManyToManyField(to='ct.Concept')),
                ('course', models.ForeignKey(to='ct.Course')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('courselet', models.ForeignKey(to='ct.Courselet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ErrorModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('isAbort', models.BooleanField(default=False)),
                ('isFail', models.BooleanField(default=False)),
                ('isPuzzled', models.BooleanField(default=False)),
                ('alwaysAsk', models.BooleanField(default=False)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concept', models.ForeignKey(to='ct.Concept', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Glossary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('explanation', models.TextField()),
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
                ('url', models.CharField(max_length=256, null=True)),
                ('kind', models.CharField(default=b'reading', max_length=10, choices=[(b'reading', b'reading'), (b'data', b'data'), (b'lecture', b'lecture'), (b'slides', b'slides'), (b'exercise', b'exercise'), (b'case', b'Case Study'), (b'project', b'project'), (b'e-pedia', b'Encyclopedia'), (b'forum', b'forum'), (b'video', b'video'), (b'audio', b'audio'), (b'image', b'image'), (b'db', b'Database'), (b'software', b'software')])),
                ('sourceDB', models.CharField(max_length=32, null=True)),
                ('sourceID', models.CharField(max_length=100, null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('rustID', models.CharField(max_length=64)),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LessonLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'defines', max_length=10, choices=[(b'is', b'Represents (unique ID)'), (b'defines', b'Defines'), (b'informal', b'Intuitive statement of'), (b'formaldef', b'Formal definition for'), (b'derives', b'Derives'), (b'proves', b'Proves'), (b'assumes', b'Assumes'), (b'motiv', b'Motivates'), (b'illust', b'Illustrates'), (b'intro', b'Introduces'), (b'comment', b'Comments on'), (b'warns', b'Warning about')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concept', models.ForeignKey(to='ct.Concept')),
                ('lesson', models.ForeignKey(to='ct.Lesson', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LiveQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('liveStage', models.IntegerField(null=True)),
                ('startTime', models.DateTimeField(null=True, verbose_name=b'time started')),
                ('aTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time started')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('courseQuestion', models.ForeignKey(to='ct.CourseQuestion')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LiveSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('startTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time started')),
                ('endTime', models.DateTimeField(null=True, verbose_name=b'time completed')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(to='ct.Course')),
                ('liveQuestion', models.ForeignKey(related_name=b'+', to='ct.LiveQuestion', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LiveUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('liveQuestion', models.ForeignKey(to='ct.LiveQuestion')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('qtext', models.TextField()),
                ('answer', models.TextField()),
                ('access', models.CharField(default=b'public', max_length=10, choices=[(b'public', b'Public'), (b'instr', b'By instructors only'), (b'CI', b'For concept inventory only'), (b'private', b'By author only')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('rustID', models.CharField(max_length=64)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('concept', models.ForeignKey(to='ct.Concept', null=True)),
                ('errorModels', models.ManyToManyField(to='ct.ErrorModel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'case', max_length=10, choices=[(b'presq', b'Presents question for'), (b'presa', b'Presents answer for'), (b'case', b'Case description for'), (b'intros', b'Introduces')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('lesson', models.ForeignKey(to='ct.Lesson')),
                ('question', models.ForeignKey(to='ct.Question')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Remediation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('advice', models.TextField()),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('errorModel', models.ForeignKey(to='ct.ErrorModel')),
                ('lessons', models.ManyToManyField(to='ct.Lesson', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Resolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default=b'explains', max_length=10, choices=[(b'explains', b'Explains'), (b'counter', b'Clear example of incorrectness of'), (b'informal', b'Intuitive statement of'), (b'formaldef', b'Formal definition for'), (b'illust', b'Illustrates'), (b'intro', b'Introduces'), (b'comment', b'Comments on'), (b'warns', b'Warns where people commonly make')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('errorModel', models.ForeignKey(to='ct.ErrorModel')),
                ('lesson', models.ForeignKey(to='ct.Lesson')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atext', models.TextField()),
                ('confidence', models.CharField(max_length=10, choices=[(b'guess', b'Just guessing'), (b'notsure', b'Not quite sure'), (b'sure', b'Pretty sure')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('selfeval', models.CharField(max_length=10, null=True, choices=[(b'different', b'Different'), (b'close', b'Close'), (b'correct', b'Essentially the same')])),
                ('status', models.CharField(max_length=10, null=True, choices=[(b'help', b'Still confused, need help'), (b'review', b'OK, but need further review and practice'), (b'done', b'Solidly')])),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('courseQuestion', models.ForeignKey(to='ct.CourseQuestion', null=True)),
                ('liveQuestion', models.ForeignKey(to='ct.LiveQuestion', null=True)),
                ('question', models.ForeignKey(to='ct.Question')),
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
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('courseErrorModel', models.ForeignKey(blank=True, to='ct.CourseErrorModel', null=True)),
                ('response', models.ForeignKey(to='ct.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.ForeignKey(to='ct.Question')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vocabulary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=100)),
                ('definition', models.TextField()),
                ('atime', models.DateTimeField(verbose_name=b'time submitted')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('glossary', models.ForeignKey(to='ct.Glossary')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='livequestion',
            name='liveSession',
            field=models.ForeignKey(to='ct.LiveSession'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lessonlink',
            name='question',
            field=models.ForeignKey(to='ct.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='coursequestion',
            name='question',
            field=models.ForeignKey(to='ct.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courselesson',
            name='courselet',
            field=models.ForeignKey(to='ct.Courselet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courselesson',
            name='lesson',
            field=models.ForeignKey(to='ct.Lesson'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courseerrormodel',
            name='courseQuestion',
            field=models.ForeignKey(to='ct.CourseQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courseerrormodel',
            name='errorModel',
            field=models.ForeignKey(to='ct.ErrorModel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conceptpicture',
            name='glossary',
            field=models.ForeignKey(to='ct.Glossary'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conceptequation',
            name='glossary',
            field=models.ForeignKey(to='ct.Glossary'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commonerror',
            name='concept',
            field=models.ForeignKey(to='ct.Concept'),
            preserve_default=True,
        ),
    ]
