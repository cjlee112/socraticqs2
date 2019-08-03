from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0020_auto_20170412_0258'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('response_report', models.FileField(null=True, upload_to='reports/responses/', blank=True)),
                ('error_report', models.FileField(null=True, upload_to='reports/errors/', blank=True)),
                ('course', models.ForeignKey(to='ct.Course', on_delete=models.CASCADE)),
            ],
        ),
    ]
