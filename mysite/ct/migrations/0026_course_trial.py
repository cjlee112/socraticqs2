from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0025_response_is_preview'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='trial',
            field=models.BooleanField(default=False),
        ),
    ]
