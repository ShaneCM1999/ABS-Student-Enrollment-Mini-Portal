import os
import sqlite3
import pymysql
import pymysql.cursors
from flask import g
from config import Config

def ensure_database_exists():
    """Ensure the MySQL database exists before opening table queries."""
    if Config.DB_TYPE == "mysql":
        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=int(Config.MYSQL_PORT),
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                charset="utf8mb4",
                connect_timeout=3
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MySQL Notice] Could not pre-create database: {e}")

def get_db():
    """
    Returns a database connection attached to Flask's 'g' context.
    Uses pure PyMySQL (DictCursor) for MySQL, or sqlite3.Row for SQLite.
    Zero ORM - 100% Raw SQL.
    """
    if "db" not in g:
        if Config.DB_TYPE == "sqlite":
            db_path = os.getenv("SQLITE_PATH", "student_portal.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name: row['first_name']
            g.db = conn
        else:
            g.db = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=int(Config.MYSQL_PORT),
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=3
            )
    return g.db

def close_db(e=None):
    """Closes the current request's database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(schema_file="schema.sql"):
    """Executes schema.sql statements directly using Raw SQL."""
    if Config.DB_TYPE == "mysql":
        ensure_database_exists()
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with conn.cursor() as cursor:
                if os.path.exists(schema_file):
                    with open(schema_file, "r", encoding="utf-8") as f:
                        sql_text = f.read()
                    # Execute individual statements separated by semicolon
                    for statement in sql_text.split(";"):
                        stmt = statement.strip()
                        if stmt and not stmt.lower().startswith("create database") and not stmt.lower().startswith("use "):
                            cursor.execute(stmt)
                conn.commit()
        finally:
            conn.close()
    else:
        # SQLite initialization with the new 4-table relational schema
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT NOT NULL PRIMARY KEY,
                full_name TEXT NOT NULL,
                grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 12),
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL DEFAULT 'Male',
                email TEXT NOT NULL UNIQUE,
                parent_name TEXT,
                parent_phone TEXT,
                status TEXT NOT NULL DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT NOT NULL PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_code TEXT NOT NULL PRIMARY KEY,
                title TEXT NOT NULL,
                grade_level INTEGER NOT NULL,
                teacher_id TEXT,
                capacity INTEGER NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_code TEXT NOT NULL,
                term TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (course_code) REFERENCES courses(course_code) ON DELETE CASCADE
            );
        """)
        db.commit()
