# Generated by Django 2.1.11 on 2019-08-14 22:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0033_auto_20190814_1537'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unit',
            old_name='assessment_name',
            new_name='exam_name',
        ),
    ]
