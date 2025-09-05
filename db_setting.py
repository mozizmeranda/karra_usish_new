import sqlite3 as sq
# import asyncpg
# import aiosqlite


class Database:

    def __init__(self, db_name="users.db"):
        self.path_to_db = db_name

    @property
    def connection(self):
        return sq.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()

        connection = self.connection
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        if commit:
            connection.commit()
        connection.close()

        return data

    def create_table(self):
        sql = ("CREATE TABLE IF NOT EXISTS Users(id INT, name TEXT, number TEXT, landing TEXT, time_slot TEXT, "
               "date TEXT)")
        self.execute(sql, commit=True)

    def insert_into_two_params(self, id: int, name: str, number: str):
        sql = "INSERT OR IGNORE INTO Users(id, name, number) VALUES (?, ?, ?)"
        parameters = (id, name, number)
        self.execute(sql, parameters=parameters, commit=True)

    def insert_into(self, id: int, name: str, number: str, landing, date, time_slot):
        sql = "INSERT OR IGNORE INTO Users(id, name, number, landing, date, time_slot) VALUES (?, ?, ?, ?, ?, ?)"
        parameters = (id, name, number, landing, date, time_slot)
        self.execute(sql, parameters=parameters, commit=True)

    def get_all_users(self):
        sql = "SELECT * FROM Users"
        data = self.execute(sql, fetchall=True)
        return data

    def get_all_users_by_landing_1(self):
        sql = "SELECT number FROM Users WHERE landing=2"
        data = self.execute(sql, fetchall=True)
        return data

    def get_all_data(self, time_slot):
        sql = "SELECT * FROM Users WHERE time_slot=?"
        params = (time_slot,)
        data = self.execute(sql, parameters=(time_slot,), fetchall=True)
        return data

    def get_user_by_id(self, id: int):
        sql = "SELECT * FROM Users WHERE id=?"
        data = self.execute(sql, (id,), fetchone=True)
        return data
    

database = Database()


