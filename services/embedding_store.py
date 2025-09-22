from services.db_connection import get_connection, release_connection
from psycopg2 import DatabaseError, OperationalError
from pgvector.psycopg2 import register_vector

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
        conn = get_connection()

        # Register pgvector on this connection
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(insert_query, (journal_id, user_id, embedding))
            conn.commit()
    except (OperationalError, DatabaseError) as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Error storing embedding: {e}")
    finally:
        if conn:
            release_connection(conn)
