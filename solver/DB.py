import pymysql

class DB:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.database = "admin_lct"
        self.connection = None

        # Establish a connection to the MySQL database
        self.connect()

    def connect(self):
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def query(self, sql, params=None):
        # Create a cursor object to execute SQL queries
        cursor = self.connection.cursor()
        # Execute the query
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        schema = []
        if(cursor.description is not None):
            schema = [column[0] for column in cursor.description]

        # Close cursor
        result = cursor.fetchall()
        cursor.close()
        return result, schema

    def __del__(self):
        if self.connection:
            self.connection.close()
