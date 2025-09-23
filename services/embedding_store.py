from services.db_connection import get_connection, release_connection
from psycopg2 import DatabaseError, OperationalError
from pgvector.psycopg2 import register_vector
import config

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
        conn = get_connection()

        # Register pgvector on this connection
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(insert_query, (summary_id, user_id, embedding))
            conn.commit()
    except (OperationalError, DatabaseError) as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Error storing embedding: {e}")
    finally:
        if conn:
            release_connection(conn)
