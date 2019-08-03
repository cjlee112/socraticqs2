from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ltiuser',
            name='django_user',
            field=models.ForeignKey(related_name='lti_auth', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
