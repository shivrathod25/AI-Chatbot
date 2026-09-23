"""
Course Enrollment Chatbot - SQL-to-Python Database Connection Engine
database.py

Contains ONLY the Python-to-MySQL connection logic for XAMPP MySQL.
Database creation, table structure, indexes, and queries are managed in XAMPP MySQL (ai_chatbot).
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("database")

# Load environment variables from backend/.env regardless of CWD
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Database configuration parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_chatbot")


def get_connection():
    """
    Establish and return a connection to XAMPP MySQL server.
    Connecting to database: ai_chatbot
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=5
        )
        return connection
    except mysql.connector.Error as err:
        logger.error(f"MySQL connection failure to {DB_HOST}:{DB_PORT}/{DB_NAME}: {err}")
        raise RuntimeError(f"Database connection error: {err}")


def get_db_health():
    """
    Check XAMPP MySQL database connectivity and report system status.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM enrollments;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "engine": "MYSQL",
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "total_enrollments": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "engine": "MYSQL",
            "database": DB_NAME
        }


if __name__ == "__main__":
    health = get_db_health()
    print(f"[OK] Database Diagnostics: {health}")