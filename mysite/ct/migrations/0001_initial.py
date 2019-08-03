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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('approvedBy', models.ForeignKey(related_name='approvedConcepts', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptGraph',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default='depends', max_length=10, choices=[('depends', 'Depends on'), ('motiv', 'Motivates'), ('errmod', 'misunderstands'), ('violates', 'Violates'), ('contains', 'Contains'), ('tests', 'Tests'), ('conflicts', 'Conflicts with'), ('proves', 'Proves'), ('dispro', 'Disproves')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('approvedBy', models.ForeignKey(related_name='approvedConceptEdges', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('fromConcept', models.ForeignKey(related_name='relatedTo', to='ct.Concept', on_delete=models.CASCADE)),
                ('toConcept', models.ForeignKey(related_name='relatedFrom', to='ct.Concept', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(default='defines', max_length=10, choices=[('is', 'Represents (unique ID)'), ('defines', 'Defines'), ('informal', 'Intuitive statement of'), ('formaldef', 'Formal definition for'), ('derives', 'Derives'), ('proves', 'Proves'), ('assumes', 'Assumes'), ('motiv', 'Motivates'), ('illust', 'Illustrates'), ('intro', 'Introduces'), ('comment', 'Comments on'), ('warns', 'Warning about')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('concept', models.ForeignKey(to='ct.Concept', on_delete=models.CASCADE)),
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
                ('access', models.CharField(default='public', max_length=10, choices=[('public', 'Public'), ('enroll', 'By instructors only'), ('private', 'By author only')])),
                ('enrollCode', models.CharField(max_length=64, null=True)),
                ('lockout', models.CharField(max_length=200, null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('course', models.ForeignKey(to='ct.Course', on_delete=models.CASCADE)),
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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('fsm', models.ForeignKey(to='ct.FSM', on_delete=models.CASCADE)),
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
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time started')),
                ('fsmNode', models.ForeignKey(to='ct.FSMNode', on_delete=models.CASCADE)),
                ('linkState', models.ForeignKey(related_name='linkChildren', to='ct.FSMState', null=True, on_delete=models.CASCADE)),
                ('parentState', models.ForeignKey(related_name='children', to='ct.FSMState', null=True, on_delete=models.CASCADE)),
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
                ('kind', models.CharField(default='base', max_length=10, choices=[('base', 'brief definition and explanation'), ('explanation', 'long explanation'), ('orct', 'Open Response Concept Test question'), ('mcct', 'Concept Inventory Test question'), ('exercise', 'exercise'), ('project', 'project'), ('practice', 'practice exam question'), ('answer', 'answer'), ('errmod', 'error model'), ('data', 'data'), ('case', 'Case Study'), ('e-pedia', 'Encyclopedia'), ('faq', 'frequently asked question'), ('forum', 'forum')])),
                ('medium', models.CharField(default='reading', max_length=10, choices=[('reading', 'reading'), ('lecture', 'lecture'), ('slides', 'slides'), ('video', 'video'), ('audio', 'audio'), ('image', 'image'), ('db', 'Database'), ('software', 'software')])),
                ('access', models.CharField(default='public', max_length=10, choices=[('public', 'Public'), ('enroll', 'By instructors only'), ('exam', 'Protected exam only'), ('private', 'By author only')])),
                ('sourceDB', models.CharField(max_length=32, null=True)),
                ('sourceID', models.CharField(max_length=100, null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('treeID', models.IntegerField(null=True)),
                ('changeLog', models.TextField(null=True)),
                ('commitTime', models.DateTimeField(null=True, verbose_name='time committed')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('mergeParent', models.ForeignKey(related_name='mergeChildren', to='ct.Lesson', null=True, on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='children', to='ct.Lesson', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default='orct', max_length=10, choices=[('orct', 'ORCT response'), ('sq', 'Question about a lesson'), ('comment', 'Reply comment')])),
                ('text', models.TextField()),
                ('confidence', models.CharField(max_length=10, choices=[('guess', 'Just guessing'), ('notsure', 'Not quite sure'), ('sure', 'Pretty sure')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('selfeval', models.CharField(max_length=10, null=True, choices=[('different', 'Different'), ('close', 'Close'), ('correct', 'Essentially the same')])),
                ('status', models.CharField(max_length=10, null=True, choices=[('help', 'Still confused, need help'), ('review', 'OK, but flag this for me to review'), ('done', 'Solidly')])),
                ('needsEval', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('course', models.ForeignKey(to='ct.Course', null=True, on_delete=models.CASCADE)),
                ('lesson', models.ForeignKey(to='ct.Lesson', on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(to='ct.Response', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(default='student', max_length=10, choices=[('prof', 'Instructor'), ('TA', 'Teaching Assistant'), ('student', 'Enrolled Student'), ('self', 'Self-study')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('course', models.ForeignKey(to='ct.Course', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudentError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('status', models.CharField(max_length=10, null=True, choices=[('help', 'Still confused, need help'), ('review', 'OK, but flag this for me to review'), ('done', 'Solidly')])),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lesson', models.ForeignKey(to='ct.Lesson', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
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
                ('kind', models.CharField(default='unit', max_length=10, choices=[('unit', 'Courselet'), ('live', 'Live session'), ('resol', 'Resolutions for an error model')])),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time created')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default='part', max_length=10, choices=[('part', 'Included in this courselet'), ('answers', 'Answer for a question'), ('errmod', 'Common error for a question'), ('pretest', 'Pre-test/Post-test for this courselet'), ('subunit', 'Container for this courselet')])),
                ('order', models.IntegerField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time added')),
                ('treeID', models.IntegerField()),
                ('branch', models.CharField(default='master', max_length=32)),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('lesson', models.ForeignKey(to='ct.Lesson', null=True, on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE)),
                ('unit', models.ForeignKey(to='ct.Unit', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='studenterror',
            name='errorModel',
            field=models.ForeignKey(blank=True, to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studenterror',
            name='response',
            field=models.ForeignKey(to='ct.Response', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='fromNode',
            field=models.ForeignKey(related_name='outgoing', to='ct.FSMNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='toNode',
            field=models.ForeignKey(related_name='incoming', to='ct.FSMNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsm',
            name='startNode',
            field=models.ForeignKey(related_name='+', to='ct.FSMNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='courseunit',
            name='unit',
            field=models.ForeignKey(to='ct.Unit', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conceptlink',
            name='lesson',
            field=models.ForeignKey(to='ct.Lesson', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
