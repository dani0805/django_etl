# Generated by Django 2.1.7 on 2019-03-04 09:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Database',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Name')),
                ('connection_string', models.CharField(max_length=2000, verbose_name='Connection String')),
                ('type', models.CharField(choices=[('mssql', 'mssql'), ('mysql', 'mysql'), ('sqlite', 'sqlite')], max_length=200, verbose_name='Database Type')),
            ],
        ),
        migrations.CreateModel(
            name='FieldMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_field', models.CharField(max_length=200, verbose_name='Source Field')),
                ('destination_field', models.CharField(max_length=200, verbose_name='Destination Field')),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Name')),
                ('active', models.BooleanField(default=True, verbose_name='Active')),
                ('source_batch_sql', models.CharField(max_length=4000, verbose_name='Source Batch SQL')),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='destination_jobs', to='etl.Database', verbose_name='Destination')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='source_job', to='etl.Database', verbose_name='Source')),
            ],
        ),
        migrations.CreateModel(
            name='JobStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_id', models.CharField(max_length=200, verbose_name='Batch Id')),
                ('status', models.CharField(choices=[('running', 'running'), ('completed', 'completed'), ('error', 'error')], max_length=200, verbose_name='Status')),
                ('started_on', models.DateTimeField(verbose_name='Started On')),
                ('completed_on', models.DateTimeField(null=True, verbose_name='Completed On')),
                ('error', models.CharField(max_length=4000, null=True, verbose_name='Batch Id')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='etl.Job', verbose_name='Job')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_table', models.CharField(max_length=200, verbose_name='Source Table')),
                ('destination_table', models.CharField(max_length=200, verbose_name='Destination Table')),
                ('filter', models.CharField(max_length=200, verbose_name='Filter')),
                ('chunk_size', models.IntegerField(verbose_name='Chunk Size')),
                ('source_batch_column', models.CharField(max_length=200, verbose_name='Source Batch Column')),
                ('destination_batch_column', models.CharField(max_length=200, verbose_name='Destination Batch Column')),
                ('active', models.BooleanField(default=True, verbose_name='Active')),
                ('truncate_on_load', models.BooleanField(default=True, verbose_name='Active')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='etl.Job', verbose_name='Job')),
            ],
        ),
        migrations.CreateModel(
            name='TaskStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_id', models.CharField(max_length=200, verbose_name='Batch Id')),
                ('status', models.CharField(choices=[('running', 'running'), ('completed', 'completed'), ('error', 'error')], max_length=200, verbose_name='Status')),
                ('started_on', models.DateTimeField(verbose_name='Started On')),
                ('completed_on', models.DateTimeField(null=True, verbose_name='Completed On')),
                ('error', models.CharField(max_length=4000, null=True, verbose_name='Batch Id')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='etl.Job', verbose_name='Job')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='etl.Task', verbose_name='Task')),
            ],
        ),
        migrations.AddField(
            model_name='fieldmapping',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='etl.Task', verbose_name='Task'),
        ),
    ]
