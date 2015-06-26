# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0015_migrate_fsm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concept',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='kind',
            field=models.CharField(default=b'base', max_length=50, choices=[(b'base', b'brief definition and explanation'), (b'explanation', b'long explanation'), (b'orct', b'Open Response Concept Test question'), (b'mcct', b'Concept Inventory Test question'), (b'exercise', b'exercise'), (b'project', b'project'), (b'practice', b'practice exam question'), (b'answer', b'answer'), (b'errmod', b'error model'), (b'data', b'data'), (b'case', b'Case Study'), (b'e-pedia', b'Encyclopedia'), (b'faq', b'frequently asked question'), (b'forum', b'forum')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
    ]
