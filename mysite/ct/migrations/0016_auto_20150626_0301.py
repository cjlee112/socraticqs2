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
            field=models.CharField(default='base', max_length=50, choices=[('base', 'brief definition and explanation'), ('explanation', 'long explanation'), ('orct', 'Open Response Concept Test question'), ('mcct', 'Concept Inventory Test question'), ('exercise', 'exercise'), ('project', 'project'), ('practice', 'practice exam question'), ('answer', 'answer'), ('errmod', 'error model'), ('data', 'data'), ('case', 'Case Study'), ('e-pedia', 'Encyclopedia'), ('faq', 'frequently asked question'), ('forum', 'forum')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
    ]
