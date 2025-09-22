from psycopg2 import pool, OperationalError
import config

# Initialize connection pool once
try:
    conn_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=config.PG_HOST,
        dbname=config.PG_DB,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        port=config.PG_PORT
    )
except OperationalError as e:
    raise ConnectionError(f"Unable to create connection pool: {e}")

def get_connection():
    """Fetch a connection from the pool"""
    return conn_pool.getconn()

def release_connection(conn):
    """Return connection back to the pool"""
    conn_pool.putconn(conn)
