from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20180530_2334'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='what_do_you_teach',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
