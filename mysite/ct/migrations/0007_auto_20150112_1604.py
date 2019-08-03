from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0006_courseunit_releasetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='fsmnode',
            name='funcName',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='path',
            field=models.CharField(default='foo', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='fsm',
            name='startNode',
            field=models.ForeignKey(related_name='+', to='ct.FSMNode', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='path',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
