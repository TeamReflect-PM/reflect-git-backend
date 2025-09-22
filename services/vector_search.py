# vector_search.py
from db_connection import get_connection, release_connection
from psycopg2 import DatabaseError, OperationalError
from pgvector.psycopg2 import register_vector

def pg_vector_search(query_embedding, user_id, top_k=50):
    """
    Cosine similarity vector search in PostgreSQL using pgvector
    """
    conn = None
    try:
        conn = get_connection()

        # Register pgvector type for this connection
        register_vector(conn)

        sql = """
        SELECT journal_id, 1 - (embedding <=> %s) AS score
        FROM journal_embeddings
        WHERE user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (query_embedding, user_id, query_embedding, top_k))
            results = cur.fetchall()

        return [{"journal_id": r[0], "score": float(r[1])} for r in results]

    except (OperationalError, DatabaseError) as e:
        raise RuntimeError(f"Error in vector search: {e}")

    finally:
        if conn:
            release_connection(conn)
