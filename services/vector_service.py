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

def store_embedding(user_id: str, summary_id: str, embedding: list, table: str = "journal_embeddings"):
    """
    Store a single embedding (journal or conversation) in PostgreSQL using connection pool.
    
    Parameters:
    - user_id: str
    - summary_id: str (journal_id or conversation summary_id)
    - embedding: list of floats
    - table: str - table name ('journal_embeddings' or 'conversation_embeddings')
    """
    if not embedding or not isinstance(embedding, list):
        raise ValueError("Embedding must be a non-empty list of floats")
    
    # Determine column name based on table
    column_id = "journal_id" if table == "journal_embeddings" else "summary_id"

    insert_query = f"""
        INSERT INTO {table} ({column_id}, user_id, embedding)
        VALUES (%s, %s, %s)
    """
    
    conn = None
    try:
        # Get a connection from the pool
        conn = conn_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(insert_query, (summary_id, user_id, embedding))
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