from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0012_auto_20150320_1414'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='title',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
    ]
