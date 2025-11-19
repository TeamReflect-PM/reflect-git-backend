from google.cloud import firestore
from datetime import datetime
import uuid
from config import PROJECT_ID

# Initialize Firestore for Project 2 (reflect-466215)
db = firestore.Client(project=PROJECT_ID)

def get_or_create_user(email, display_name=None):
    """
    Gets existing user or creates new user in Project 2 database.
    This function is called whenever a user (authenticated in Project 1) 
    interacts with our backend services.
    
    Args:
        email: User email from Firebase Auth (Project 1)
        display_name: Optional display name
    
    Returns:
        dict: User data from Project 2 database
    """
    try:
        # Check if user exists in Project 2 database
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.stream()
        
        user_doc = None
        for doc in docs:
            user_doc = doc
            break
            
        if user_doc:
            # User exists, return existing data
            user_data = user_doc.to_dict()
            user_data['user_id'] = user_doc.id
            
            # Update last active timestamp
            user_doc.reference.update({
                'last_active': datetime.now()
            })
            
            print(f"DEBUG: Found existing user: {email} -> {user_data['user_id']}")
            return user_data
        else:
            # User doesn't exist, create new user in Project 2
            new_user_data = {
                'email': email,
                'display_name': display_name or email.split('@')[0],
                'created_at': datetime.now(),
                'last_active': datetime.now(),
                'journal_count': 0,
                'conversation_count': 0,
                'preferences': {
                    'theme': 'default',
                    'notifications': True,
                    'privacy_level': 'standard'
                }
            }
            
            # Add to Firestore in Project 2
            doc_ref = users_ref.add(new_user_data)
            user_id = doc_ref[1].id
            
            new_user_data['user_id'] = user_id
            print(f"DEBUG: Created new user: {email} -> {user_id}")
            return new_user_data
            
    except Exception as e:
        print(f"Error in get_or_create_user: {str(e)}")
        raise e

def update_user_activity(email):
    """
    Updates user's last activity timestamp.
    Called on each API interaction.
    """
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.stream()
        
        for doc in docs:
            doc.reference.update({
                'last_active': datetime.now()
            })
            break
            
    except Exception as e:
        print(f"Error updating user activity: {str(e)}")

def increment_user_stats(email, stat_type):
    """
    Increments user statistics (journal_count, conversation_count).
    
    Args:
        email: User email
        stat_type: 'journal' or 'conversation'
    """
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.stream()
        
        for doc in docs:
            if stat_type == 'journal':
                doc.reference.update({
                    'journal_count': firestore.Increment(1)
                })
            elif stat_type == 'conversation':
                doc.reference.update({
                    'conversation_count': firestore.Increment(1)
                })
            break
            
    except Exception as e:
        print(f"Error incrementing user stats: {str(e)}")

def get_user_profile(email):
    """
    Gets complete user profile from Project 2 database.
    """
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.stream()
        
        for doc in docs:
            user_data = doc.to_dict()
            user_data['user_id'] = doc.id
            return user_data
            
        return None
        
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None

def update_user_preferences(email, preferences):
    """
    Updates user preferences in Project 2 database.
    """
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.stream()
        
        for doc in docs:
            doc.reference.update({
                'preferences': preferences,
                'updated_at': datetime.now()
            })
            return True
            
        return False
        
    except Exception as e:
        print(f"Error updating user preferences: {str(e)}")
        return False

def get_user_id_from_email(email):
    """
    Helper function to get Project 2 user ID from email.
    Used by other services that need the internal user ID.
    """
    try:
        user_data = get_or_create_user(email)
        return user_data['user_id']
    except Exception as e:
        print(f"Error getting user ID from email: {str(e)}")
        return None