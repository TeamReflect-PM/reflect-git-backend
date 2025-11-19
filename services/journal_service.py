import vertexai
from vertexai.generative_models import GenerativeModel
from services.create_embedding import get_embedding
from services.embedding_store import store_embedding
from services.user_service import get_or_create_user, increment_user_stats
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
    Bridges Project 1 (auth) with Project 2 (storage).
    Raises exceptions on server errors.
    Returns True if success.
    """
    # Client-side validation
    journal_text = data.get("journal_text")
    user_email = data.get("user_id")  # This is actually the email from Project 1

    if not journal_text or not user_email:
        raise ValueError("user_id (email) and journal_text are required")

    # BRIDGE: Get or create user in Project 2
    user_data = get_or_create_user(user_email)
    internal_user_id = user_data['user_id']  # Project 2 user ID
    
    print(f"DEBUG: Journal storage - Email: {user_email} -> Internal ID: {internal_user_id}")

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

        # Save to Firestore under users/{internalUserId}/journals/{journalId}
        db.collection("users").document(internal_user_id).collection("journals").document(journal_id).set({
            "journal_text": journal_text,
            "summary": result["summary"],
            "metadata": result["metadata"],
            "user_email": user_email,  # Store original email for reference
            "created_at": datetime.utcnow()
        })

        
        #Embedding and Vector DB
        try:
            embedding = get_embedding(result["summary"])
            if not isinstance(embedding, list) or not all(isinstance(x, float) for x in embedding):
                raise ValueError(f"Invalid embedding returned: {embedding}")
        except Exception as e:
                raise RuntimeError(f"Embedding generation failed: {e}")

        # Store embedding with email as user_id for consistency with existing vector search
        store_embedding(user_email, journal_id, embedding, "journal_embeddings")
        
        # Update user statistics
        increment_user_stats(user_email, 'journal')

        return {"status": "success"}, 200
        
    except Exception as e:
        # Any unexpected exception → raise for API route to handle
        raise RuntimeError(f"Error storing journal: {str(e)}")


def fetch_summaries_and_metadata(user_email: str, journal_ids: list[str]) -> list[dict]:
    """
    Fetch summaries + metadata for a given user email and list of journal_ids.
    Bridges Project 1 (email) with Project 2 (internal user ID).

    Args:
        user_email (str): The email of the user from Project 1.
        journal_ids (list[str]): List of journal IDs to fetch.

    Returns:
        list[dict]: A list of dictionaries with journal_id, summary, and metadata.
    """
    if not user_email or not journal_ids:
        raise ValueError("Both user_email and journal_ids are required")

    try:
        # BRIDGE: Get internal user ID from email
        user_data = get_or_create_user(user_email)
        internal_user_id = user_data['user_id']
        
        results = []
        journals_ref = db.collection("users").document(internal_user_id).collection("journals")

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
        print(f"Error fetching summaries/metadata for user {user_email}: {str(e)}")
        raise RuntimeError("Failed to fetch summaries and metadata") from e

def get_journals_summary_by_ids(user_email, journal_ids):
    """
    Retrieves summary and metadata for specified journal IDs for a given user.
    Bridges Project 1 (email) with Project 2 (internal user ID).
    Returns a list of journal data (summary + metadata) for the requested journal IDs.
    """
    try:
        # BRIDGE: Get internal user ID from email
        user_data = get_or_create_user(user_email)
        internal_user_id = user_data['user_id']
        
        journals_data = []
        
        for journal_id in journal_ids:
            # Get journal document from Firestore using internal user ID
            journal_ref = db.collection("users").document(internal_user_id).collection("journals").document(journal_id)
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

def get_all_journals_by_user(user_email, limit=50):
    """
    Retrieves all journals for a given user email.
    Bridges Project 1 (email) with Project 2 (internal user ID).
    Returns a list of journal entries with summaries and metadata.
    """
    try:
        # BRIDGE: Get internal user ID from email
        user_data = get_or_create_user(user_email)
        internal_user_id = user_data['user_id']

        # Get all journals for this user, ordered by creation date (newest first)
        journals_ref = db.collection("users").document(internal_user_id).collection("journals")
        journals_query = journals_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        journals_docs = journals_query.stream()

        journals_data = []
        for doc in journals_docs:
            doc_data = doc.to_dict()
            journal_entry = {
                "journal_id": doc.id,
                "journal_text": doc_data.get("journal_text"),
                "summary": doc_data.get("summary"),
                "metadata": doc_data.get("metadata"),
                "created_at": doc_data.get("created_at")
            }
            journals_data.append(journal_entry)

        return utils.make_serializable(journals_data)

    except Exception as e:
        raise RuntimeError(f"Error retrieving all journals for user {user_email}: {str(e)}")
