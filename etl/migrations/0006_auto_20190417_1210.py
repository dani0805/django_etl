# Generated by Django 2.0.1 on 2019-04-17 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etl', '0005_job_shares_loadid_with'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='shares_loadid_with',
            field=models.ManyToManyField(to='etl.Job'),
        ),
    ]
