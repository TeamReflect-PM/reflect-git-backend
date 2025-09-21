from psycopg2 import pool, OperationalError, DatabaseError
from pgvector.psycopg2 import register_vector
import config

# Initialize connection pool
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

# Register pgvector type on all pool connections
try:
    conn = conn_pool.getconn()
    register_vector(conn)
finally:
    if conn:
        conn_pool.putconn(conn)

def store_embedding(journal_id: str, user_id: str, embedding: list):
    """
    Store a single journal embedding in PostgreSQL using connection pool.
    """
    if not embedding or not isinstance(embedding, list):
        raise ValueError("Embedding must be a non-empty list of floats")

    insert_query = """
        INSERT INTO journal_embeddings (journal_id, user_id, embedding)
        VALUES (%s, %s, %s)
    """

    conn = None
    try:
        # Get a connection from the pool
        conn = conn_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(insert_query, (journal_id, user_id, embedding))
            conn.commit()
    except (OperationalError, DatabaseError) as e:
        # Rollback in case of DB error
        if conn:
            conn.rollback()
        raise RuntimeError(f"Error storing embedding: {e}")
    finally:
        # Return connection back to pool
        if conn:
            conn_pool.putconn(conn)
