from django.db import models
from django.utils.translation import ugettext_lazy

# Create your models here.


class Database(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name=ugettext_lazy("Name"))
    connection_string = models.CharField(max_length=2000, verbose_name=ugettext_lazy("Connection String"))
    type = models.CharField(choices=(("mssql", "mssql"), ("mysql", "mysql"), ("sqlite", "sqlite")), verbose_name=ugettext_lazy("Database Type"))


class Job(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name=ugettext_lazy("Name"))
    source = models.ForeignKey(Database, verbose_name=ugettext_lazy("Source"))
    destination = models.ForeignKey(Database, verbose_name=ugettext_lazy("Destination"))


class Task(models.Model):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"))
    source_table = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Table"))
    destination_table = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Table"))
    filter = models.CharField(max_length=200, verbose_name=ugettext_lazy("Filter"))
    chunk_size = models.IntegerField(verbose_name=ugettext_lazy("Chunk Size"))
    source_batch_column = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Batch Column"))
    destination_batch_column = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Batch Column"))

    @property
    def extract_query(self):
        return "select {} from {}".format(", ".join(self.fieldmapping_set.all()), self.source_table)

    @property
    def load_query(self):
        return "insert into {} values (\{\})".format(self.destination_table)


class FieldMapping(models.Model):
    task = models.ForeignKey(Task, verbose_name=ugettext_lazy("Task"))
    source_field = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Field"))
    destination_field = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Field"))


class JobStatus(models):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"))
    batch_id = models.CharField(max_length=200, verbose_name=ugettext_lazy("Batch Id"))
    status = models.CharField(choices=(("running", "running"), ("completed", "completed"), ("error", "error")), verbose_name=ugettext_lazy("Status"))
    started_on = models.DateTimeField(verbose_name=ugettext_lazy("Started On"))
    completed_on = models.DateTimeField(null=True, verbose_name=ugettext_lazy("Completed On"))
    error = models.CharField(max_length=4000, null=True, verbose_name=ugettext_lazy("Batch Id"))


class TaskStatus(models):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"))
    task = models.ForeignKey(Task, verbose_name=ugettext_lazy("Task"))
    batch_id = models.CharField(max_length=200, verbose_name=ugettext_lazy("Batch Id"))
    status = models.CharField(choices=(("running", "running"), ("completed", "completed"), ("error", "error")), verbose_name=ugettext_lazy("Status"))
    started_on = models.DateTimeField(verbose_name=ugettext_lazy("Started On"))
    completed_on = models.DateTimeField(null=True, verbose_name=ugettext_lazy("Completed On"))
    error = models.CharField(max_length=4000, null=True, verbose_name=ugettext_lazy("Batch Id"))
