from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_auto_20161116_0755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='state',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fsm.FSMState'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, null=True),
            preserve_default=True,
        ),
    ]
