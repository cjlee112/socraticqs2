from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0023_course_copied_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='attachment',
            field=models.FileField(null=True, upload_to='questions', blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='enable_auto_grading',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_max_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_min_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=50, null=True, choices=[('choices', 'Multiple Choices Question'), ('numbers', 'Numbers'), ('equation', 'Equation'), ('canvas', 'Canvas')]),
        ),
        migrations.AddField(
            model_name='response',
            name='attachment',
            field=models.FileField(null=True, upload_to='answers', blank=True),
        ),
        migrations.AddField(
            model_name='response',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='response',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[('choices', 'Multiple Choices response'), ('numbers', 'Numbers response'), ('equation', 'Equation response'), ('canvas', 'Canvas response')]),
        ),
        migrations.AlterField(
            model_name='course',
            name='title',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex='^\\s+?$', message='This field can not consist of only spaces', inverse_match=True)]),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='title',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex='^\\s+?$', message='This field can not consist of only spaces', inverse_match=True)]),
        ),
        migrations.AlterField(
            model_name='unit',
            name='title',
            field=models.CharField(help_text='Your students will see this, so give your courselet a descriptive name.', max_length=200, validators=[django.core.validators.RegexValidator(regex='^\\s+?$', message='This field can not consist of only spaces', inverse_match=True)]),
        ),
    ]
