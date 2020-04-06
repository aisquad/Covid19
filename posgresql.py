from psycopg2 import connect, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DataBase:
    def __init__(self):
        self.conn = connect(
            database= "covid19",
            user="postgres",
            host='',
            password='^PostGres#49$'
        )
        self.cursor = None

    def __create(self, database_name):
        self.connect()
        self.cursor.execute(f"SELECT * FROM pg_catalog.pg_database")
        if database_name in [r[1] for r in self.cursor.fetchall()]:
            return
        self.cursor.execute(f"CREATE DATABASE {database_name}")

    def create_database_if_doesnt_exist(self, dn_name):
        self.__create(dn_name)

    def connect(self):
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def create_table(self, table_name, ):
        self.connect()
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} ("
            "id int,"
            "name text,"
            "primary key (id)"
            ")"
        )

    def close(self):
        self.cursor.close()
        self.conn.close()

    def insert(self, table, values):
        self.cursor.execute(
            f"INSERT INTO {table} (VALUES ("
            f"0, 'Albania'  ))"
        )

if __name__ == "__main__":
    db = DataBase()
    db.create_database_if_doesnt_exist('covid19')
    db.create_table('countries')
    db.close()

