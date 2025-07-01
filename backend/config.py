import os
import urllib.parse
from dotenv import load_dotenv # type: ignore

load_dotenv()

DB_USER = urllib.parse.quote_plus(os.getenv("DB_USER", "postgres"))
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "password"))
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ma_base")

USE_SQL_SERVER = os.getenv("USE_SQL_SERVER", "false").lower() == "true"

if USE_SQL_SERVER:
    DATABASE_URL = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST},{DB_PORT}/{DB_NAME}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )
else:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print("DATABASE_URL =", DATABASE_URL)