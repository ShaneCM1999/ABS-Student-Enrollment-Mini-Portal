import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "abs-portal-secret-key-super-secure-2026")
    
    # Database Engine Configuration (Pure Raw SQL - No ORM)
    raw_db_type = os.getenv("DB_TYPE", "sqlite").lower().strip()
    DB_TYPE = "sqlite" if "sqlite" in raw_db_type else "mysql"
    
    # MySQL Connection Parameters
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "student_portal")
    
    # SQLite Path (for local/offline mode)
    SQLITE_PATH = os.getenv("SQLITE_PATH", "student_portal.db")
