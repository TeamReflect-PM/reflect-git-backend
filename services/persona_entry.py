import json
from google.cloud import firestore
from datetime import datetime
from services import utils
from services.user_service import get_or_create_user
from config import PROJECT_ID  # Config file for project settings

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID)


def store_persona_entry(data):
    """
    Stores a user's persona entry as-is in Firestore without any summarization or metadata processing.
    Stores as a single persona document per user (not in a collection).
    Bridges Project 1 (auth) with Project 2 (storage).
    Raises exceptions on server errors.
    Returns True if success.
    """
    print(f"DEBUG: store_persona_entry called with data: {data}")

    # Client-side validation
    persona_data = data.get("persona")
    user_email = data.get("user_id")  # This is actually the email from Project 1

    print(f"DEBUG: user_email: {user_email}")
    print(f"DEBUG: persona_data exists: {bool(persona_data)}")

    if not persona_data or not user_email:
        print(f"DEBUG: Validation failed - user_email: {user_email}, persona_data: {bool(persona_data)}")
        raise ValueError("user_id (email) and persona are required")

    # BRIDGE: Get or create user in Project 2
    user_data = get_or_create_user(user_email)
    internal_user_id = user_data['user_id']  # Project 2 user ID

    print(f"DEBUG: Persona storage - Email: {user_email} -> Internal ID: {internal_user_id}")

    try:
        # Prepare persona document with timestamp
        persona_document = {
            "persona": persona_data,
            "user_email": user_email,  # Store original email for reference
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }

        # Add persona_metadata if it exists in the input
        if "persona_metadata" in data:
            persona_document["persona_metadata"] = data["persona_metadata"]

        print(f"DEBUG: About to save persona document for internal_user_id: {internal_user_id}")
        print(f"DEBUG: Document path: users/{internal_user_id}/profile/persona")

        # Save to Firestore as a single document under users/{internalUserId}/profile/persona
        db.collection("users").document(internal_user_id).collection("profile").document("persona").set(persona_document)

        print(f"DEBUG: Successfully saved persona to Firestore for user: {user_email}")
        return {"status": "success"}, 200

    except Exception as e:
        print(f"DEBUG: Exception occurred while saving persona: {str(e)}")
        # Any unexpected exception → raise for API route to handle
        raise RuntimeError(f"Error storing persona: {str(e)}")

def get_persona_by_user_id(user_email):
    """
    Retrieves a user's persona from Firestore.
    Bridges Project 1 (email) with Project 2 (internal user ID).
    Returns the persona data if found, None otherwise.
    """
    if not user_email:
        raise ValueError("user_email is required")

    try:
        # BRIDGE: Get internal user ID from email
        user_data = get_or_create_user(user_email)
        internal_user_id = user_data['user_id']

        print(f"DEBUG: Persona retrieval - Email: {user_email} -> Internal ID: {internal_user_id}")

        # Get persona document from Firestore using internal user ID
        persona_ref = db.collection("users").document(internal_user_id).collection("profile").document("persona")
        persona_doc = persona_ref.get()

        if persona_doc.exists:
            return utils.make_serializable(persona_doc.to_dict())
        else:
            return None

    except Exception as e:
        raise RuntimeError(f"Error retrieving persona: {str(e)}")
