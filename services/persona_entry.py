import json
from google.cloud import firestore
from datetime import datetime
from config import PROJECT_ID  # Config file for project settings

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID)


def store_persona_entry(data):
    """
    Stores a user's persona entry as-is in Firestore without any summarization or metadata processing.
    Stores as a single persona document per user (not in a collection).
    Raises exceptions on server errors.
    Returns True if success.
    """
    # Client-side validation
    persona_data = data.get("persona")
    user_id = data.get("user_id")

    if not persona_data or not user_id:
        raise ValueError("user_id and persona are required")

    try:
        # Prepare persona document with timestamp
        persona_document = {
            "persona": persona_data,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }

        # Add persona_metadata if it exists in the input
        if "persona_metadata" in data:
            persona_document["persona_metadata"] = data["persona_metadata"]

        # Save to Firestore as a single document under users/{userId}/profile/persona
        db.collection("users").document(user_id).collection("profile").document("persona").set(persona_document)

        return {"status": "success"}, 200
        
    except Exception as e:
        # Any unexpected exception � raise for API route to handle
        raise RuntimeError(f"Error storing persona: {str(e)}")