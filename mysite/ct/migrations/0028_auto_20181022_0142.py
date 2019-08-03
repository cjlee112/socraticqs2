from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0027_auto_20180904_1112'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='mc_simplified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='add_unit_aborts',
            field=models.BooleanField(default=False),
        ),
    ]
