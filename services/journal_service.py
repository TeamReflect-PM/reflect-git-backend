import vertexai
from vertexai.generative_models import GenerativeModel
from services.embedding_service import get_embedding
from services.vector_service import store_embedding
import json, uuid
from google.cloud import firestore
from datetime import datetime
from config import PROJECT_ID, REGION  # Config file for project settings

# Initialize VertexAI + Firestore
vertexai.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel("gemini-2.5-flash")
db = firestore.Client(project=PROJECT_ID)


def analyze_store_and_embed_journal(data):
    """
    Stores a user's journal entry along with summary and metadata in Firestore.
    Raises exceptions on server errors.
    Returns True if success.
    """
    # Client-side validation
    journal_text = data.get("journal_text")
    user_id = data.get("user_id")

    if not journal_text or not user_id:
        raise ValueError("user_id and journal_text are required")

    try:
        # ---------------- PROMPT ----------------
        prompt = f"""
You are analyzing a personal journal entry.

Journal Entry:
{journal_text}

TASK:

1. Create a concise summary that is shorter than the original journal.
   - Include only key points: main events, people, places, dates, emotions, and activities.
   - Remove unnecessary details, repetitions, and explanations.
   - Keep it concise (max 70% of original length).

2. Return a JSON object with:
{{
    "summary": "the concise summary",
    "metadata": {{
        "date": "YYYY-MM-DD if mentioned, else null",
        "mood": "overall emotional tone",
        "people": ["max 3 most important people"],
        "topics": ["max 3 main themes"],
        "emotions": ["max 3 main emotions"],
        "activities": ["max 3 main activities"],
        "stress_level": "low, medium, or high"
    }}
}}

For the metadata fields (people, topics, emotions, activities):
- Include **at most 3 items per list**.
- Only include the most relevant and important ones.
- Do not include minor or irrelevant items.
"""
        # Call Gemini model
        response = model.generate_content(prompt)
        text_output = response.candidates[0].content.parts[0].text

        try:
            result = json.loads(text_output)
        except json.JSONDecodeError:
            cleaned = text_output.strip().strip("```json").strip("```")
            result = json.loads(cleaned)

        # Generate journal ID
        journal_id = str(uuid.uuid4())

        # Save to Firestore under users/{userId}/journals/{journalId}
        db.collection("users").document(user_id).collection("journals").document(journal_id).set({
            "journal_text": journal_text,
            "summary": result["summary"],
            "metadata": result["metadata"],
            "created_at": datetime.utcnow()
        })

        
        #Embedding and Vector DB
        embedding = get_embedding(result["summary"])
        #print("Embedding:", embedding)

        #upsert_embedding(journal_id,user_id, embedding)
        store_embedding(journal_id,user_id, embedding, "journal_embeddings")

        return {"status": "success"}, 200
        
    except Exception as e:
        # Any unexpected exception → raise for API route to handle
        raise RuntimeError(f"Error storing journal: {str(e)}")


def fetch_summaries_and_metadata(user_id: str, journal_ids: list[str]) -> list[dict]:
    """
    Fetch summaries + metadata for a given user_id and list of journal_ids.

    Args:
        user_id (str): The ID of the user.
        journal_ids (list[str]): List of journal IDs to fetch.

    Returns:
        list[dict]: A list of dictionaries with journal_id, summary, and metadata.
    """
    if not user_id or not journal_ids:
        raise ValueError("Both user_id and journal_ids are required")

    try:
        results = []
        journals_ref = db.collection("users").document(user_id).collection("journals")

        for jid in journal_ids:
            doc = journals_ref.document(jid).get()
            if doc.exists:
                data = doc.to_dict()
                results.append({
                    "journal_id": jid,
                    "summary": data.get("summary"),
                    "metadata": data.get("metadata")
                })
            else:
                results.append({
                    "journal_id": jid,
                    "error": "Journal not found"
                })

        return results

    except Exception as e:
        print(f"Error fetching summaries/metadata for user {user_id}: {str(e)}")
        raise RuntimeError("Failed to fetch summaries and metadata") from e
