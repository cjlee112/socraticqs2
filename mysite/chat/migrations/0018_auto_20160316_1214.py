# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0017_message_is_additional'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='fsm_state',
            new_name='state',
        ),
    ]
