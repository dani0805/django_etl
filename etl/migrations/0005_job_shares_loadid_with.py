# Generated by Django 2.0.1 on 2019-04-17 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etl', '0004_auto_20190320_1100'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='shares_loadid_with',
            field=models.ManyToManyField(blank=True, null=True, to='etl.Job'),
        ),
    ]
