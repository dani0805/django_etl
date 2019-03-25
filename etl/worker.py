import json

import sys

try:
    import MySQLdb as mysql
except:
    print("No mysql driver found ... ")
try:
    import pyodbc
except:
    print("No odbc driver found ... ")
try:
    import sqlite3
except:
    print("No sqlite driver found ... ")


from django.utils.timezone import now

from etl.models import Job, Database, JobStatus, TaskStatus, Task


class Worker:

    def __init__(self, *, job: Job):
        self.job = job

    def run(self) -> int:

        # connect to source
        source_connection = self.connect(db=self.job.source)

        # connect to destination
        target_connection = self.connect(db=self.job.destination)
        # query source batch
        b_cursor = source_connection.cursor()
        b_cursor.execute(self.job.next_source_batch_sql)
        batch_id = b_cursor.fetchone()

        try:
            # return if no such batch is found
            if batch_id is None or len(batch_id) == 0 or batch_id[0] is None:
                return 0
            else:
                batch_id = batch_id[0]

            # return if batch is already being processed otherwise log batch as in progress
            if JobStatus.objects.filter(job=self.job, batch_id=batch_id).exists():
                return 0
            else:
                try:
                    JobStatus.objects.create(job=self.job, batch_id=batch_id, started_on=now(), status="running")
                except Exception as ce:
                    raise SystemError(
                        "Could not create job status log for batch id \n{} \nand job \n{}\n This error was caused by \n{}\n{}".format(
                            batch_id, self.job, ce, sys.exc_info()[2]
                        )
                    )

            # loop through task
            for task in self.job.task_set.filter(active=True):
                self.run_task(task=task, target_connection=target_connection, source_connection=source_connection, batch_id=batch_id)

            # log batch completed
            JobStatus.objects.filter(job=self.job, batch_id=batch_id, status="running").update(completed_on=now(),
                status="completed")

        except Exception as e:
            JobStatus.objects.filter(job=self.job, batch_id=batch_id, status="running").update(
                error="Error executing Job: {}\n{}".format(e, sys.exc_info()[2])[:3998],
                completed_on=now(),
                status="error")

            raise
        finally:
            source_connection.close()
            target_connection.close()
        return 1

    def run_task(self, *, task: Task, source_connection, target_connection, batch_id: str):
        # log target start
        if TaskStatus.objects.filter(job=self.job, task=task, batch_id=batch_id).exists():
            return 0
        else:
            TaskStatus.objects.create(job=self.job, task=task, batch_id=batch_id, started_on=now(), status="running")

        s_cursor = source_connection.cursor()
        t_cursor = target_connection.cursor()
        try:
            # truncate target if required
            self.truncate_target_table(target_connection=target_connection, task=task)
            target_connection.commit()
            s_cursor.execute(task.extract_query(batch_id=batch_id))
            # select next chunk to memory
            data = s_cursor.fetchmany(task.chunk_size) if task.chunk_size > 0 else s_cursor.fetchall()
            # while there are chunks left
            while data:
                # write chunk to destination
                query = task.load_query(batch_id=batch_id)
                last_bracket = query.rfind("(")
                values_template = str(query[last_bracket:])
                values = ", ".join([values_template.format(*[
                    a.replace("'", "''") if isinstance(a, str) else a for a in row
                ]) for row in data])
                query = str(query[:last_bracket]) + values
                try:
                    t_cursor.execute(query)
                except Exception as err:
                    raise SystemError(
                        "could not insert data with query \n{}\n This error was caused by \n{}\n{}".format(
                            query, err, sys.exc_info()[2]
                        )
                    )
                target_connection.commit()
                # select next chunk to memory
                data = s_cursor.fetchmany(task.chunk_size) if task.chunk_size > 0 else None
                # log target end
            TaskStatus.objects.filter(job=self.job, task=task, batch_id=batch_id, status="running").update(
                completed_on=now(),
                status="completed")
        except Exception as e:
            TaskStatus.objects.filter(job=self.job, task=task, batch_id=batch_id, status="running").update(
                error="Error executing Task: {}\n{}".format(e, sys.exc_info()[2])[:3998],
                completed_on=now(),
                status="error")
            raise
        finally:
            s_cursor.close()
            t_cursor.close()




    def truncate_target_table(self, *, target_connection, task):
        if task.truncate_on_load:
            tr_cursor = target_connection.cursor()
            if self.job.destination.type == "sqlite":
                tr_cursor.execute("delete from {}".format(task.destination_table))
            else:
                tr_cursor.execute("truncate table {}".format(task.destination_table))
            tr_cursor.close()

    def connect(self, *, db: Database):
        connect_string = json.loads(db.connection_string)
        #print(connect_string)
        #print(db.type)

        if db.type == 'mysql':
            return mysql.connect(**connect_string)
        elif db.type == 'mssql':
            return pyodbc.connect(**connect_string)
        elif db.type == 'sqlite':
            return sqlite3.connect(**connect_string)
        else:
            raise ValueError("Invalid database type {}".format(self.job.source.type))