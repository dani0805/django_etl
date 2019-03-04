from django.db import models
from django.db.models import PROTECT
from django.utils.translation import ugettext_lazy


# Create your models here.


class Database(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name=ugettext_lazy("Name"))
    connection_string = models.CharField(max_length=2000, verbose_name=ugettext_lazy("Connection String"))
    type = models.CharField(max_length=200, choices=(("mssql", "mssql"), ("mysql", "mysql"), ("sqlite", "sqlite")),
        verbose_name=ugettext_lazy("Database Type"))


class Job(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name=ugettext_lazy("Name"))
    source = models.ForeignKey(Database, verbose_name=ugettext_lazy("Source"), related_name="source_job",
        on_delete=PROTECT)
    destination = models.ForeignKey(Database, verbose_name=ugettext_lazy("Destination"),
        related_name="destination_jobs", on_delete=PROTECT)
    active = models.BooleanField(default=True, verbose_name=ugettext_lazy("Active"))
    source_batch_sql = models.CharField(max_length=4000, unique=True, verbose_name=ugettext_lazy("Source Batch SQL"))

    @property
    def next_source_batch_sql(self):
        last_batch = JobStatus.objects.filter(status="completed").order_by("id").first()
        if last_batch is None:
            last_batch = "none"
        return self.source_batch_sql.format(last_batch)



class Task(models.Model):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"), on_delete=PROTECT)
    source_table = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Table"))
    destination_table = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Table"))
    filter = models.CharField(max_length=200, null=True, verbose_name=ugettext_lazy("Filter"))
    chunk_size = models.IntegerField(verbose_name=ugettext_lazy("Chunk Size"))
    source_batch_column = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Batch Column"))
    destination_batch_column = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Batch Column"))
    active = models.BooleanField(default=True, verbose_name=ugettext_lazy("Active"))
    truncate_on_load = models.BooleanField(default=True, verbose_name=ugettext_lazy("Active"))

    def extract_query(self, *, batch_id: str):
        fields = ", ".join(self.fieldmapping_set.all().order_by("id").values_list("source_field", flat=True))
        return "select {} from {} where {} = '{}'{}{}".format(
            fields,
            self.source_table,
            self.source_batch_column,
            batch_id,
            " and " if self.filter else "",
            self.filter if self.filter else "")

    def load_query(self, *, batch_id: str):
        field_list = self.fieldmapping_set.all().order_by("id").values_list("destination_field", flat=True)
        fields = ", ".join(field_list)
        return "insert into {} ({},{}) values ({},{})".format(
            self.destination_table,
            self.destination_batch_column,
            fields,
            batch_id,
            ", ".join(["?" for i in range(len(field_list))])
        )


class FieldMapping(models.Model):
    task = models.ForeignKey(Task, verbose_name=ugettext_lazy("Task"), on_delete=PROTECT)
    source_field = models.CharField(max_length=200, verbose_name=ugettext_lazy("Source Field"))
    destination_field = models.CharField(max_length=200, verbose_name=ugettext_lazy("Destination Field"))


class JobStatus(models.Model):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"), on_delete=PROTECT)
    batch_id = models.CharField(max_length=200, verbose_name=ugettext_lazy("Batch Id"))
    status = models.CharField(max_length=200,
        choices=(("running", "running"), ("completed", "completed"), ("error", "error")),
        verbose_name=ugettext_lazy("Status"))
    started_on = models.DateTimeField(verbose_name=ugettext_lazy("Started On"))
    completed_on = models.DateTimeField(null=True, verbose_name=ugettext_lazy("Completed On"))
    error = models.CharField(max_length=4000, null=True, verbose_name=ugettext_lazy("Batch Id"))


class TaskStatus(models.Model):
    job = models.ForeignKey(Job, verbose_name=ugettext_lazy("Job"), on_delete=PROTECT)
    task = models.ForeignKey(Task, verbose_name=ugettext_lazy("Task"), on_delete=PROTECT)
    batch_id = models.CharField(max_length=200, verbose_name=ugettext_lazy("Batch Id"))
    status = models.CharField(max_length=200,
        choices=(("running", "running"), ("completed", "completed"), ("error", "error")),
        verbose_name=ugettext_lazy("Status"))
    started_on = models.DateTimeField(verbose_name=ugettext_lazy("Started On"))
    completed_on = models.DateTimeField(null=True, verbose_name=ugettext_lazy("Completed On"))
    error = models.CharField(max_length=4000, null=True, verbose_name=ugettext_lazy("Batch Id"))
