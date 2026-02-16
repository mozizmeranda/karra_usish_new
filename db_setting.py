import aiosqlite


class Database:

    def __init__(self, db_name="users.db"):
        self.path_to_db = db_name

    async def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()

        async with aiosqlite.connect(self.path_to_db) as connection:
            cursor = await connection.cursor()
            data = None
            await cursor.execute(sql, parameters)

            if fetchone:
                data = await cursor.fetchone()
            if fetchall:
                data = await cursor.fetchall()
            if commit:
                await connection.commit()

            return data

    async def create_table(self):
        sql = "CREATE TABLE IF NOT EXISTS Users(id INT PRIMARY KEY, name TEXT, number TEXT)"
        await self.execute(sql, commit=True)

    async def insert_into(self, telegram_id: int, name: str, number: str):
        sql = "INSERT OR REPLACE INTO Users(id, name, number) VALUES (?, ?, ?)"
        parameters = (telegram_id, name, number)
        await self.execute(sql, parameters=parameters, commit=True)

    async def get_all_users(self):
        sql = "SELECT * FROM Users"
        data = await self.execute(sql, fetchall=True)
        return data

    async def get_all_ids(self):
        sql = "SELECT id FROM Users"
        data = await self.execute(sql, fetchall=True)
        return data

    async def get_user_by_id(self, telegram_id: int):
        sql = "SELECT * FROM Users WHERE id=?"
        data = await self.execute(sql, (telegram_id,), fetchone=True)
        return data

    async def delete_user(self, telegram_id: int):
        sql = "DELETE FROM Users WHERE id=?"
        await self.execute(sql, (telegram_id,), commit=True)


database = Database()
