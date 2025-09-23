import uuid
from datetime import datetime
import json
from google.cloud import firestore
from vertexai.generative_models import GenerativeModel
from services.create_embedding import get_embedding
from services.embedding_store import store_embedding
from google.protobuf.timestamp_pb2 import Timestamp
from config import PROJECT_ID, REGION
from services import utils

# Initialize Firestore + VertexAI
db = firestore.Client(project=PROJECT_ID)
model = GenerativeModel("gemini-2.5-flash")


def summarize_and_store_conversation(user_id: str, user_message: str, ai_response: str):
    """
    Summarizes a conversation turn (user + AI), stores summary + metadata in Firestore,
    generates embedding, and stores it in PostgreSQL for top-k retrieval.
    Returns the summary_id.
    """

    # ---------------- PROMPT FOR SUMMARIZATION ----------------
    prompt = f"""
You are summarizing a single conversation turn between a user and AI therapist.
Combine user message and AI response into a concise summary (max 50 words).
Return a JSON object with:
{{
    "summary": "...",
    "metadata": {{
        "mood": "overall emotional tone",
        "topics": ["max 3 main topics"],
        "emotions": ["max 3 main emotions"],
        "stress_level": "low, medium, high"
    }}
}}
User: "{user_message}"
AI: "{ai_response}"
"""

    # Call Gemini
    response = model.generate_content(prompt)
    text_output = response.candidates[0].content.parts[0].text

    # ---------------- PARSE SUMMARY ----------------
    try:
        result = json.loads(text_output)
    except json.JSONDecodeError:
        cleaned = text_output.strip().strip("```json").strip("```")
        result = json.loads(cleaned)

    # ---------------- STORE SUMMARY IN FIRESTORE ----------------
    summary_id = str(uuid.uuid4())
    db.collection("users").document(user_id)\
      .collection("conversation_summary").document(summary_id).set({
        "summary_text": result["summary"],
        "metadata": result["metadata"],
        "user_message": user_message,
        "ai_response": ai_response,
        "created_at": datetime.utcnow()
    })

    # ---------------- CREATE EMBEDDING AND STORE IN POSTGRES ----------------
    embedding_vector = get_embedding(result["summary"])
    store_embedding(
        user_id=user_id,
        summary_id=summary_id,
        embedding=embedding_vector,
        table="conversation_embeddings"
    )

    return summary_id


def get_latest_n_summaries(user_id: str, n: int = 3):
    """
    Fetch the latest N conversation summaries for a user.
    Returns a list of dictionaries with summary and metadata.
    """
    summaries_ref = db.collection("users").document(user_id)\
                      .collection("conversation_summary")\
                      .order_by("created_at", direction="DESCENDING")\
                      .limit(n).stream()

    result = []
    for doc in summaries_ref:
        data = doc.to_dict()
        
        result.append({
            "summary_text": data.get("summary_text"),
            "metadata": data.get("metadata")
        })

    return utils.make_serializable(result)

