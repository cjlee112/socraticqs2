from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ctms', '0004_bestpractice1_bestpractice2'),
        ('ct', '0031_auto_20190711_0545'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='best_practice1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ctms.BestPractice1'),
        ),
    ]
