# Generated by Django 2.1.12 on 2019-11-25 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0040_auto_20191121_0539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='error_resolution_days',
            field=models.IntegerField(blank=True, default=2, null=True),
        ),
    ]
