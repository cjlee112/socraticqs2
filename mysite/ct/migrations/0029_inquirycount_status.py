from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0028_auto_20181022_0142'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquirycount',
            name='status',
            field=models.CharField(choices=[('help', 'Still confused, need help'), ('review', 'OK, but flag this for me to review'), ('done', 'Solidly')], max_length=10, null=True),
        ),
    ]
