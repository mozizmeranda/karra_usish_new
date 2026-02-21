import aiosqlite


class Database:

    def __init__(self, db_name="users.db"):
        self.path_to_db = db_name
        self._connection: aiosqlite.Connection = None

    async def connect(self):
        self._connection = await aiosqlite.connect(self.path_to_db)
        # self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA synchronous=NORMAL")

    async def close(self):
        if self._connection:
                await self._connection.close()

    async def execute(self, sql, parameters=None, fetchone=False, fetchall=False, commit=False):
        parameters = parameters or tuple()
        cursor = await self._connection.execute(sql, parameters)
        data = None
        if fetchone:
            data = await cursor.fetchone()
        if fetchall:
            data = await cursor.fetchall()
        if commit:
            await self._connection.commit()
        return data

    async def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            number TEXT,
            reminder_step INTEGER DEFAULT 0,
            next_reminder_at TEXT
        )
        """
        await self.execute(sql, commit=True)

        # Создаём индекс для ускорения поиска пользователей с напоминаниями
        sql_index = "CREATE INDEX IF NOT EXISTS idx_next_reminder ON Users(next_reminder_at)"
        await self.execute(sql_index, commit=True)

    async def insert_into(self, telegram_id: int, name: str, number: str,
                          reminder_step: int = 0, next_reminder_at: str = None):
        sql = """
        INSERT OR REPLACE INTO Users(id, name, number, reminder_step, next_reminder_at)
        VALUES (?, ?, ?, ?, ?)
        """
        parameters = (telegram_id, name, number, reminder_step, next_reminder_at)
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

    async def checkpoint(self):
        await self._connection.execute("PRAGMA wal_checkpoint(FULL)")
        await self._connection.commit()

    # ----------------------------------   REMINDERS   ---------------------------------
    async def stop_reminders(self, telegram_id: int):
        sql = """
        UPDATE Users
        SET reminder_step = 99, next_reminder_at = NULL
        WHERE id = ?
        """
        await self.execute(sql, parameters=(telegram_id,), commit=True)


database = Database()
