# Generated by Django 2.1.11 on 2019-08-14 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ctms', '0006_auto_20190812_0041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestpractice',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ct.Course'),
        ),
        migrations.AlterField(
            model_name='bestpractice',
            name='courselet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ct.Unit'),
        ),
    ]
