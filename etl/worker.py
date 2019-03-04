import json

import mysql.connector
import pyodbc
import sqlite3

from django.utils.timezone import now

from etl.models import Job, Database, JobStatus


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
        b_cursor.execute(self.job.source_batch_sql)
        batch_id = b_cursor.fetchone()[0]

        # return if batch is already being processed otherwise log batch as in progress
        if JobStatus.objects.filter(job=self.job, batch_id=batch_id).exists():
            return 0
        else:
            JobStatus.objects.create(job=self.job, batch_id=batch_id, started_on=now(), status="running")

        # loop through task
        for task in self.job.task_set.filter(active=True):
            s_cursor = source_connection.cursor()
            t_cursor = target_connection.cursor()
            # truncate target if required
            if task.truncate_on_load:
                tr_cursor = target_connection.cursor()
                tr_cursor.execute("truncate table {}".format(task.destination_table))
                tr_cursor.close()

            # while there are chunks left
            s_cursor.execute(task.extract_query(batch_id=batch_id))
            # select next chunk to memory
            data = s_cursor.fetchmany(size=task.chunk_size) if task.chunk_size > 0 else s_cursor.fetchall()
            while data:
                # write chunk to destination
                t_cursor.executemany(task.load_query(batch_id=batch_id), data)
                data = s_cursor.fetchmany(size=task.chunk_size) if task.chunk_size > 0 else None
            s_cursor.close()
            t_cursor.close()

        # log batch completed
        JobStatus.objects.filter(job=self.job, batch_id=batch_id, status="running").update(comleted_on=now(), status="completed")

        return 1

    def connect(self, *, db: Database):
        connect_string = json.loads(db.connection_string)
        if db.type == 'mysql':
            return mysql.connector.connect(**connect_string)
        elif db.type == 'mssql':
            return pyodbc.connect(**connect_string)
        elif db.type == 'sqlite':
            return sqlite3.connect(**connect_string)
        else:
            raise ValueError("Invalid database type {}".format(self.job.source.type))