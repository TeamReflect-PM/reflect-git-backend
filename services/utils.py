from datetime import datetime

def make_serializable(obj):
    """
    Recursively converts Firestore timestamps (DatetimeWithNanoseconds) or Python datetimes
    into ISO strings so that json.dumps can serialize the object.
    Works on dictionaries, lists, and nested structures.
    """
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif hasattr(obj, "isoformat"):  # Handles both datetime and Firestore timestamp objects
        return obj.isoformat()
    else:
        return obj