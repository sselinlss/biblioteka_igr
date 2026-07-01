import sqlite3
import os

DB_PATH = "data/games.db"


class DatabaseManager:
    def __init__(self):
        self.conn = None

    def init_db(self):
        # создаю папку data и таблицу
        os.makedirs("data", exist_ok=True)

        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform TEXT,
                hours INTEGER DEFAULT 0,
                status TEXT,
                rating INTEGER DEFAULT 5,
                image_path TEXT
            )
        """)
        self.conn.commit()

    def get_all_games(self, platform_filter=None):
        # фильтр по платформе
        cursor = self.conn.cursor()

        if platform_filter:
            cursor.execute(
                "SELECT * FROM games WHERE platform = ? ORDER BY title",
                (platform_filter,)
            )
        else:
            cursor.execute("SELECT * FROM games ORDER BY title")

        return cursor.fetchall()

    def get_game_by_id(self, game_id):
        # получение игры по ID
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        return cursor.fetchone()

    def insert_game(self, data):
        # добавление новой игры
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO games (title, platform, hours, status, rating, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["title"],
            data["platform"],
            data["hours"],
            data["status"],
            data["rating"],
            data.get("image_path", "")
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_game(self, data):
        # обновление данных об уже имеющейся
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE games 
            SET title=?, platform=?, hours=?, status=?, rating=?, image_path=?
            WHERE id=?
        """, (
            data["title"],
            data["platform"],
            data["hours"],
            data["status"],
            data["rating"],
            data.get("image_path", ""),
            data["id"]
        ))
        self.conn.commit()

    def delete_game(self, game_id):
        # удаление игры
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
        self.conn.commit()

    def close(self):
        # закрытие соединения с бд
        if self.conn:
            self.conn.close()