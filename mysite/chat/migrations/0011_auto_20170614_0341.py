from django.db import models, migrations


def update_last_modify_timestamp(apps, schema_editor):
    Chat = apps.get_model('chat', 'Chat')
    for chat in Chat.objects.all():
        if not chat.last_modify_timestamp:
            last_msg = chat.message_set.all().order_by('-timestamp').first()
            if last_msg:
                chat.last_modify_timestamp = last_msg.timestamp
                chat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_auto_20170613_0632'),
    ]

    operations = [
        migrations.RunPython(update_last_modify_timestamp, lambda apps, se: None),
    ]
