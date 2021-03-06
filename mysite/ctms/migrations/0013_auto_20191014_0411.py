# Generated by Django 2.1.12 on 2019-10-14 11:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ctms', '0012_bestpractice_upload_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestpractice',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ctms.BestPracticeTemplate'),
        ),
        migrations.AlterField(
            model_name='bestpracticetemplate',
            name='summary',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
