# Generated by Django 2.1.15 on 2020-01-06 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0015_auto_20190529_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_new',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='message',
            name='sub_kind',
            field=models.CharField(choices=[('add_faq', 'add_faq'), ('transition', 'transition')], max_length=32, null=True),
        ),
    ]