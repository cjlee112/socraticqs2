from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0013_chat_is_trial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(choices=[('base', 'base'), ('orct', 'orct'), ('answer', 'answer'), ('errmod', 'errmod'), ('chatdivider', 'chatdivider'), ('uniterror', 'uniterror'), ('response', 'response'), ('message', 'message'), ('button', 'button'), ('abort', 'abort')], max_length=32, null=True),
        ),
    ]
