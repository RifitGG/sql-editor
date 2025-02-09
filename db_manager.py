# db_manager.py
import sqlite3
from typing import List, Any

class DBManager:
    """
    Класс для работы с SQLite базой данных.
    """
    def __init__(self) -> None:
        self.conn: sqlite3.Connection | None = None
        self.db_file: str | None = None

    def new_database(self, filename: str) -> None:
        """Создаёт новую базу данных."""
        self.conn = sqlite3.connect(filename)
        self.db_file = filename

    def open_database(self, filename: str) -> None:
        """Открывает существующую базу данных."""
        self.conn = sqlite3.connect(filename)
        self.db_file = filename

    def export_sql(self) -> str:
        """Возвращает SQL-дамп базы данных."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        return "\n".join(self.conn.iterdump())

    def execute_script(self, script: str) -> None:
        """Выполняет SQL‑скрипт (возможно, содержащий несколько команд)."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        cur = self.conn.cursor()
        cur.executescript(script)
        self.conn.commit()

    def get_tables(self) -> List[str]:
        """Возвращает список таблиц в базе данных."""
        if not self.conn:
            return []
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cur.fetchall()]

    def drop_table(self, table_name: str) -> None:
        """Удаляет таблицу из базы данных."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        cur = self.conn.cursor()
        cur.execute(f"DROP TABLE {table_name}")
        self.conn.commit()

    def get_table_info(self, table_name: str) -> List[Any]:
        """
        Возвращает информацию о столбцах таблицы.
        Каждый кортеж: (cid, name, type, notnull, dflt_value, pk)
        """
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return cur.fetchall()

    def get_table_rows(self, table_name: str) -> List[Any]:
        """Возвращает все строки таблицы с использованием rowid."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        cur = self.conn.cursor()
        cur.execute(f"SELECT rowid, * FROM {table_name}")
        return cur.fetchall()

    def insert_row(self, table_name: str, columns: List[str], values: List[Any]) -> None:
        """Вставляет новую строку в таблицу."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        placeholders = ", ".join("?" for _ in values)
        cols = ", ".join(columns)
        sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        self.conn.commit()

    def update_row(self, table_name: str, columns: List[str], values: List[Any], rowid: int) -> None:
        """Обновляет строку таблицы по rowid."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        set_clause = ", ".join(f"{col}=?" for col in columns)
        sql = f"UPDATE {table_name} SET {set_clause} WHERE rowid=?"
        cur = self.conn.cursor()
        cur.execute(sql, values + [rowid])
        self.conn.commit()

    def delete_row(self, table_name: str, rowid: int) -> None:
        """Удаляет строку из таблицы по rowid."""
        if not self.conn:
            raise Exception("Нет подключения к базе данных.")
        sql = f"DELETE FROM {table_name} WHERE rowid=?"
        cur = self.conn.cursor()
        cur.execute(sql, (rowid,))
        self.conn.commit()
