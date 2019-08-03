from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_landingplugin_text_button'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingplugin',
            name='block_color',
            field=models.CharField(default='bg-primary', max_length=20, choices=[('bg-primary', 'blue'), ('bg-danger', 'red'), ('bg-success', 'green'), ('bg-info', 'light-blue'), ('bg-warning', 'yellow')]),
            preserve_default=True,
        ),
    ]
