import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

class MySqlHelper:
    def __init__(self):
        self.host = os.environ.get("MYSQL_HOST")
        self.user = os.environ.get("MYSQL_USER")
        self.password = os.environ.get("MYSQL_PASS") or os.environ.get("MYSQL_PASSWORD")
        self.database = os.environ.get("MYSQL_DB")
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                db=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as err:
            print("Please export MySQL Credential in your OS environment")
            print(f"Error: {err}")
            self.connection = None

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.fetchall()
        except pymysql.Error as err:
            print(f"Error: {err}")
            return None

