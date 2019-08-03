from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_auto_20181116_0657'),
        ('ctms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='enroll_unit_code',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.EnrollUnitCode'),
        ),
    ]
