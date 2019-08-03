from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fsm', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fsmedge',
            name='name',
            field=models.CharField(max_length=64, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmgroup',
            name='group',
            field=models.CharField(max_length=64, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='name',
            field=models.CharField(max_length=64, db_index=True),
            preserve_default=True,
        ),
    ]
