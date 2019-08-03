from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('default', '0001_initial'),
        ('psa', '0002_usersession'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecondaryEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, verbose_name='Secondary Email')),
                ('provider', models.ForeignKey(to='social_django.UserSocialAuth', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='secondary', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='secondaryemail',
            unique_together=set([('provider', 'email')]),
        ),
    ]
