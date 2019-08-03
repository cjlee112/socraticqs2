from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0024_auto_20180512_1527'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectnessMeter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('correctness', models.CharField(max_length=25, choices=[('correct', 'correct'), ('partially_correct', 'partially correct'), ('not_correct', 'not correct')])),
                ('points', models.FloatField(default=0)),
                ('response', models.ForeignKey(to='ct.Response', on_delete=models.CASCADE)),
            ],
        ),
    ]
