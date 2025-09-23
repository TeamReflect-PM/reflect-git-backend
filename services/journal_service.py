import vertexai
from vertexai.generative_models import GenerativeModel
from services.create_embedding import get_embedding
from services.embedding_store import store_embedding
import json, uuid
from google.cloud import firestore
from datetime import datetime
from services import utils
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
        "mood": "overall emotional tone (happy, sad, anxious, calm, etc.)",
        "people": ["max 3 important names"],
        "tags": ["topics, themes, or activities"],
        "emotions": ["max 3 specific emotions"],
        "stress_level": "low, medium, high"
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
        try:
            embedding = get_embedding(result["summary"])
            if not isinstance(embedding, list) or not all(isinstance(x, float) for x in embedding):
                raise ValueError(f"Invalid embedding returned: {embedding}")
        except Exception as e:
                raise RuntimeError(f"Embedding generation failed: {e}")

        #upsert_embedding(journal_id,user_id, embedding)
        store_embedding(journal_id,user_id, embedding, "journal_embeddings")
        store_embedding(journal_id,user_id, embedding)

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

        return utils.make_serializable(results)

    except Exception as e:
        print(f"Error fetching summaries/metadata for user {user_id}: {str(e)}")
        raise RuntimeError("Failed to fetch summaries and metadata") from e

def get_journals_summary_by_ids(user_id, journal_ids):
    """
    Retrieves summary and metadata for specified journal IDs for a given user.
    Returns a list of journal data (summary + metadata) for the requested journal IDs.
    """
    try:
        journals_data = []
        
        for journal_id in journal_ids:
            # Get journal document from Firestore
            journal_ref = db.collection("users").document(user_id).collection("journals").document(journal_id)
            journal_doc = journal_ref.get()
            
            if journal_doc.exists:
                doc_data = journal_doc.to_dict()
                # Return only summary and metadata (excluding full journal_text for efficiency)
                journal_summary = {
                    "journal_id": journal_id,
                    "summary": doc_data.get("summary"),
                    "metadata": doc_data.get("metadata"),
                    "created_at": doc_data.get("created_at")
                }
                journals_data.append(journal_summary)
            else:
                # Include info about missing journals
                journals_data.append({
                    "journal_id": journal_id,
                    "error": "Journal not found"
                })
        
        return journals_data
        
    except Exception as e:
        raise RuntimeError(f"Error retrieving journals: {str(e)}")

def make_serializable(obj):
    """
    Recursively converts Firestore timestamps (DatetimeWithNanoseconds) into ISO strings
    so that json.dumps can serialize the object.
    """
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif hasattr(obj, "isoformat"):  # Handles datetime and Firestore timestamp
        return obj.isoformat()
    else:
        return obj