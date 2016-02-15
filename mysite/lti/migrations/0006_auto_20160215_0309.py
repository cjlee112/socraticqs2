# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def create_first_lti_consumer(apps, schema_editor):
    """
    Creates LtiConsumer instance from extistent LTI settings.
    """
    LtiConsumer = apps.get_model("lti", "LtiConsumer")
    consumer_key = settings.CONSUMER_KEY
    lti_secret = settings.LTI_SECRET
    LtiConsumer.objects.get_or_create(
        consumer_name='CCLE Main',
        consumer_key=consumer_key,
        consumer_secret=lti_secret
    )


def remove_first_lti_consumer(apps, schema_editor):
    """
    Removes LtiConsumer.
    """
    LtiConsumer = apps.get_model("lti", "LtiConsumer")
    lti_secret = LtiConsumer.objects.filter(consumer_name='CCLE Main').first()
    if lti_secret:
        lti_secret.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0005_lticonsumer'),
    ]

    operations = [
        migrations.RunPython(
            create_first_lti_consumer,
            remove_first_lti_consumer
        ),
    ]
