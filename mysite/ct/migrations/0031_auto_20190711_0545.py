import ct.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0030_course_students_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='assessment_name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='unit',
            name='best_practice_type',
            field=models.CharField(blank=True, choices=[('practice', 'Practice-exam'), ('prereq', 'Prereq inventory'), ('mission', 'Mission training'), ('in_class', 'In-class')], max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='unit',
            name='deadline',
            field=models.IntegerField(blank=True, null=True, validators=[ct.models.percent_validator]),
        ),
        migrations.AddField(
            model_name='unit',
            name='durations',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='unit',
            name='follow_up_assessment_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='unit',
            name='follow_up_assessment_grade',
            field=models.IntegerField(blank=True, null=True, validators=[ct.models.percent_validator]),
        ),
        migrations.AddField(
            model_name='unit',
            name='participation_credit',
            field=models.IntegerField(blank=True, null=True, validators=[ct.models.percent_validator]),
        ),
        migrations.AddField(
            model_name='unit',
            name='practice_questions',
            field=models.FileField(blank=True, null=True, upload_to='practice_questions/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'docx'])]),
        ),
    ]
