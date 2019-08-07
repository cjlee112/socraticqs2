from django.db import models, migrations
import lti.utils


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0004_auto_20150716_0259'),
    ]

    operations = [
        migrations.CreateModel(
            name='LtiConsumer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('consumer_name', models.CharField(unique=True, max_length=255)),
                ('consumer_key', models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=32, db_index=True)),
                ('consumer_secret', models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=32)),
                ('instance_guid', models.CharField(max_length=255, unique=True, null=True, blank=True)),
                ('expiration_date', models.DateField(null=True, verbose_name='Consumer Key expiration date', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='ltiuser',
            name='lti_consumer',
            field=models.ForeignKey(to='lti.LtiConsumer', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        )
    ]
