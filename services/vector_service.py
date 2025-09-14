import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2 import OperationalError, DatabaseError
import config

def get_conn():
    """Get PostgreSQL connection with PGVector registered."""
    try:
        conn = psycopg2.connect(
            host=config.PG_HOST,
            dbname=config.PG_DB,
            user=config.PG_USER,
            password=config.PG_PASSWORD,
            port=config.PG_PORT
        )
        register_vector(conn)
        return conn
    except OperationalError as e:
        raise ConnectionError(f"Unable to connect to PostgreSQL: {e}")

def store_embedding(journal_id: str, user_id: str, embedding: list):
    """
    Store a single journal embedding in PostgreSQL.
    
    Args:
        journal_id (str): Unique ID of the journal.
        user_id (str): ID of the user.
        embedding (list[float]): 1536-dimensional embedding vector.
    """
    if not embedding or not isinstance(embedding, list):
        raise ValueError("Embedding must be a non-empty list of floats")

    insert_query = """
    INSERT INTO journal_embeddings (journal_id, user_id, embedding)
    VALUES (%s, %s, %s)
"""

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_query, (journal_id, user_id, embedding))
                conn.commit()
    except (OperationalError, DatabaseError) as e:
        raise RuntimeError(f"Error storing embedding: {e}")
