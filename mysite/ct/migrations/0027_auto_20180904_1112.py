from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0026_course_trial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='FSM_flow',
            field=models.CharField(choices=[('chat', 'Default FSM flow'), ('chat_trial', 'Trial FSM flow - ABORTS before Student answer')], default='chat', max_length=10),
        ),
        migrations.AddField(
            model_name='response',
            name='is_trial',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='trial_mode',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='unit',
            name='is_show_will_learn',
            field=models.BooleanField(default=False),
        ),
    ]
