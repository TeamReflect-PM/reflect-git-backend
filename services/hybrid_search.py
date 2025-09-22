# search/hybrid_search.py
"""
Hybrid search (vector + metadata) using PostgreSQL (pgvector) and Firestore.
This version fixes the operator mismatch error by casting the embedding string to vector.
"""

from typing import List, Dict, Any
from services.db_connection import get_connection, release_connection
from google.cloud import firestore
import logging

db = firestore.Client()
logger = logging.getLogger(__name__)


def _format_embedding_for_pg(embedding: List[float]) -> str:
    """Convert a Python list of floats into Postgres vector literal string"""
    elems = ",".join(repr(float(x)) for x in embedding)
    return f"[{elems}]"


def vector_search(user_id: str, query_embedding: List[float], top_k: int = 5) -> List[str]:
    """Vector similarity search"""
    conn = None
    try:
        emb_literal = _format_embedding_for_pg(query_embedding)
        conn = get_connection()
        with conn.cursor() as cur:
            sql = """
                SELECT journal_id, 1 - (embedding <=> %s::vector) AS similarity
                FROM journal_embeddings
                WHERE user_id = %s
                ORDER BY similarity DESC
                LIMIT %s
            """
            cur.execute(sql, (emb_literal, user_id, top_k))
            rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        if conn:
            release_connection(conn)


def metadata_search(user_id: str, metadata_filters: Dict[str, Any], top_k: int = 5) -> List[str]:
    """Metadata filtering via Firestore"""
    if not metadata_filters:
        return []

    coll = db.collection("users").document(user_id).collection("journals")
    query = coll

    if metadata_filters.get("people"):
        query = query.where("metadata.people", "array_contains_any", metadata_filters["people"])
    if metadata_filters.get("emotions"):
        query = query.where("metadata.emotions", "array_contains_any", metadata_filters["emotions"])
    if metadata_filters.get("tags"):
        query = query.where("metadata.tags", "array_contains_any", metadata_filters["tags"])
    if metadata_filters.get("date"):
        query = query.where("metadata.date", "==", metadata_filters["date"])
    if metadata_filters.get("mood"):
        query = query.where("metadata.mood", "==", metadata_filters["mood"])
    if metadata_filters.get("stress_level"):
        query = query.where("metadata.stress_level", "==", metadata_filters["stress_level"])

    docs = query.limit(top_k).stream()
    return [doc.id for doc in docs]


def hybrid_search(user_id: str, query_embedding: List[float], metadata_filters: Dict[str, Any], top_k: int = 5) -> List[str]:
    """Combine vector + metadata search results"""
    vector_results = vector_search(user_id, query_embedding, top_k=top_k * 2)
    metadata_results = metadata_search(user_id, metadata_filters, top_k=top_k * 2)

    combined_scores = {}
    for jid in vector_results:
        combined_scores[jid] = combined_scores.get(jid, 0) + 1
    for jid in metadata_results:
        combined_scores[jid] = combined_scores.get(jid, 0) + 2

    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [jid for jid, _ in ranked]
