# Generated by Django 2.1.12 on 2019-11-19 08:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0038_auto_20191117_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='title',
            field=models.CharField(blank=True, help_text='Your students will see this, so give your courselet a descriptive name.', max_length=200, validators=[django.core.validators.RegexValidator(inverse_match=True, message='This field can not consist of only spaces', regex='^\\s+?$')]),
        ),
    ]