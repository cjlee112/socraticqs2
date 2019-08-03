from django.db import models, migrations
import analytics.models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_coursereport_addedby'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursereport',
            name='error_report',
            field=models.FileField(null=True, upload_to=analytics.models.UploadTo('reports/errors/'), blank=True),
        ),
        migrations.AlterField(
            model_name='coursereport',
            name='response_report',
            field=models.FileField(null=True, upload_to=analytics.models.UploadTo('reports/responses'), blank=True),
        ),
    ]
