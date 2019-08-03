from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='parent',
            field=models.ForeignKey(to='ct.Response', null=True, on_delete=models.CASCADE),
        ),
    ]
