from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0029_inquirycount_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='students_number',
            field=models.PositiveIntegerField(blank=True, default=200, null=True),
        ),
    ]
