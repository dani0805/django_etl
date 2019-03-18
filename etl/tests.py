from django.test import TestCase
import sqlite3
from sqlite3 import Error
import os

from etl.models import Database, Job, Task, FieldMapping
from etl.worker import Worker


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return None


# Create your tests here.
class ETLTest(TestCase):
    source_file_name = "/tmp/source.sqlite3"
    dest_file_name = "/tmp/dest.sqlite3"

    def setUp(self):

        self.s_con = create_connection(self.source_file_name)
        cursor = self.s_con.cursor()
        cursor.execute("create table A (a_batch varchar(100), S1 varchar(200), S3 integer, S2 varchar(200))")
        cursor.execute("create table C (a_batch varchar(100), S1 varchar(200), S2 varchar(200), S3 integer)")
        for i in range(97):
            cursor.execute("insert into A (a_batch, S1, S2, S3) values ('1', 'test value {}', 'qwe', 123)".format(i))
            cursor.execute("insert into C (a_batch, S1, S2, S3) values ('1', 'test value {}', 'qwe', 234)".format(i))
        self.s_con.commit()
        cursor.close()
        self.d_con = create_connection(self.dest_file_name)
        dcursor = self.d_con.cursor()
        dcursor.execute("create table B (b_batch varchar(100), D3 integer, D2 varchar(200), D1 varchar(200))")
        dcursor.execute("create table D (b_batch varchar(100), D3 integer, D1 varchar(200), D2 varchar(200))")
        dcursor.close()
        self.s_con.close()
        self.d_con.close()

        source_db = Database.objects.create(
            name="test-source",
            connection_string="{{\"database\": \"{}\" }}".format(self.source_file_name),
            type="sqlite"
        )
        dest_db = Database.objects.create(
            name="test-dest",
            connection_string="{{\"database\": \"{}\" }}".format(self.dest_file_name),
            type="sqlite"
        )
        job = Job.objects.create(
            source=source_db,
            destination=dest_db,
            name="test-job",
            source_batch_sql="select '1' as dummy where '{}' < '1' or '{}' = 'none'"
        )
        task = Task.objects.create(
            job=job,
            source_table="A",
            destination_table="B",
            source_batch_column="a_batch",
            destination_batch_column="b_batch",
            chunk_size=10,
            filter="1=1",
            truncate_on_load=True
        )
        FieldMapping.objects.create(source_field="S1", destination_field="D1", task=task)
        FieldMapping.objects.create(source_field="S2", destination_field="D2", task=task)
        FieldMapping.objects.create(source_field="S3", destination_field="D3", task=task)

        task2 = Task.objects.create(
            job=job,
            source_table="C",
            destination_table="D",
            source_batch_column="a_batch",
            destination_batch_column="b_batch",
            chunk_size=-1,
            filter=None,
            truncate_on_load=False
        )
        FieldMapping.objects.create(source_field="S1", destination_field="D1", task=task2)
        FieldMapping.objects.create(source_field="S2", destination_field="D2", task=task2)
        FieldMapping.objects.create(source_field="S3", destination_field="D3", task=task2)


    def tearDown(self):
        os.remove(self.source_file_name)
        os.remove(self.dest_file_name)

    def test_setup(self):
        self.s_con = create_connection(self.source_file_name)
        cursor = self.s_con.cursor()
        cursor.execute("select count(1) from A")
        data = cursor.fetchone()
        self.assertEqual(data[0], 97)
        cursor.close()
        self.s_con.close()

    def test_job(self):
        worker = Worker(job=Job.objects.get(name="test-job"))
        result = worker.run()
        self.assertEqual(result, 1)
        self.d_con = create_connection(self.dest_file_name)
        c = self.d_con.cursor()
        c.execute("select count(1) from B")
        data = c.fetchone()
        self.assertEqual(data[0], 97)
        c.execute("select count(1) from D")
        data = c.fetchone()
        self.assertEqual(data[0], 97)
        c.execute("select D1, D2, D3 from D where D1 = 'test value 12'")
        data = c.fetchone()
        self.assertEqual(data[1], 'qwe')
        self.assertEqual(data[2], 234)
        result = worker.run()
        self.assertEqual(result, 0)
        c.close()
        self.d_con.close()
