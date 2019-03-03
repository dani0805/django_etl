import json

import mysql.connector
import pyodbc
import sqlite3

from etl.models import Job, Database


class Worker:

    def __init__(self, job:Job):
        self.job = job

    def run(self):

        # connect to source
        source_connection = self.connect(self.job.source)

        # connect to destination
        target_connection = self.connect(self.job.destination)

        # loop through task
        for task in self.job.task_set.all():
            s_cursor = source_connection.cursor()
            t_cursor = target_connection.cursor()
            # while there are chunks left
            s_cursor.execute(task.extract_query)
            # select next chunk to memory
            data = s_cursor.fetchmany(size=task.chunk_size) if task.chunk_size > 0 else s_cursor.fetchall()
            while data:
                # write chunk to destination
                t_cursor.executemany(task.load_query, data)
                data = s_cursor.fetchmany(size=task.chunk_size) if task.chunk_size > 0 else None
            s_cursor.close()
            t_cursor.close()

        pass

    def connect(self, db:Database):
        connect_string = json.loads(db.connection_string)
        if db.type == 'mysql':
            return mysql.connector.connect(**connect_string)
        elif db.type == 'mssql':
            return pyodbc.connect(**connect_string)
        elif db.type == 'sqlite':
            return sqlite3.connect(**connect_string)
        else:
            raise ValueError("Invalid database type {}".format(self.job.source.type))