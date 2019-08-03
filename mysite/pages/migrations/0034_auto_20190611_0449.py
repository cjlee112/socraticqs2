from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0033_keynoteplugin_keynotessetplugin_proofplugin_socialproofsplugin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keynoteplugin',
            name='uid',
            field=models.SlugField(max_length=8),
        ),
    ]
