from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_auto_20181116_0657'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='sub_kind',
            field=models.CharField(choices=[('add_faq', 'add_faq')], max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(choices=[('base', 'base'), ('orct', 'orct'), ('answer', 'answer'), ('errmod', 'errmod'), ('ask_faq_understanding', 'ask_faq_understanding'), ('chatdivider', 'chatdivider'), ('uniterror', 'uniterror'), ('response', 'response'), ('add_faq', 'add_faq'), ('message', 'message'), ('button', 'button'), ('abort', 'abort'), ('faqs', 'faqs'), ('faq', 'faq')], max_length=32, null=True),
        ),
    ]
