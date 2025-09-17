from dotenv import load_dotenv
import os

# Load .env automatically
load_dotenv()


# config.py
PROJECT_ID = "reflect-466215"
REGION = "us-central1"
EMBEDDING_MODEL = "text-embedding-005"
#Postgres SQL connection
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_DB = os.getenv("PG_DB", "reflect_db")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "Reflect@123")
PG_PORT = int(os.getenv("PG_PORT", 5432))
