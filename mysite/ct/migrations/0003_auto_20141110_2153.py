from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0002_auto_20141110_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conceptlink',
            name='relationship',
            field=models.CharField(default='defines', max_length=10, choices=[('is', 'Represents (unique ID for)'), ('defines', 'Defines'), ('informal', 'Intuitive statement of'), ('formaldef', 'Formal definition for'), ('tests', 'Tests understanding of'), ('derives', 'Derives'), ('proves', 'Proves'), ('assumes', 'Assumes'), ('motiv', 'Motivates'), ('illust', 'Illustrates'), ('intro', 'Introduces'), ('comment', 'Comments on'), ('warns', 'Warning about')]),
        ),
    ]
