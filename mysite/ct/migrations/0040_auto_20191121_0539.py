# Generated by Django 2.1.12 on 2019-11-21 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0039_auto_20191119_0029'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unit',
            name='courselet_deadline',
        ),
        migrations.AddField(
            model_name='unit',
            name='courselet_deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]