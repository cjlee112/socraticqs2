from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ctms', '0003_auto_20181129_0610'),
    ]

    operations = [
        migrations.CreateModel(
            name='BestPractice1',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_count', models.IntegerField(verbose_name='How many students do you have in your class?')),
                ('misconceptions_count', models.IntegerField(verbose_name='How many individual student misconceptions in your class did you fix today (or your average teaching day)?')),
                ('question_count', models.IntegerField(verbose_name='Number of question-parts in your typical exam (e.g. 8 questions with 3 parts each = 24)?')),
                ('mean_percent', models.IntegerField(verbose_name='Mean percent score on this exam?')),
                ('activate', models.BooleanField()),
                ('estimated_blindspots', models.IntegerField(blank=True)),
                ('estimated_blindspots_courselets', models.IntegerField(blank=True)),
                ('pdf', models.FileField(blank=True, null=True, upload_to='best_practices/', validators=[django.core.validators.FileExtensionValidator(['pdf'])])),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BestPractice2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percent_engaged', models.IntegerField(verbose_name='What percent of students are fully engaged, i.e. would immediately do any optional exercises you provide, just to improve their understanding?')),
                ('activate', models.BooleanField()),
                ('estimated_blindspots', models.IntegerField(blank=True)),
                ('estimated_blindspots_courselets', models.IntegerField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
