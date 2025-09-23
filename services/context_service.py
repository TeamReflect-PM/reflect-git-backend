# context_service.py
import requests

PERSONA_API = "http://localhost:8000/persona/"
TOPK_JOURNALS_API = "http://localhost:8000/topk_journals/"
JOURNAL_SUMMARIES_API = "http://localhost:8000/journal_summaries"

def get_persona(user_id: str):
    response = requests.get(f"{PERSONA_API}{user_id}")
    response.raise_for_status()
    return response.json()

def get_topk_journal_ids(user_id: str, query: str):
    """
    Fetch top-k journal IDs relevant to the current user query.
    """
    payload = {"user_id": user_id, "query": query}
    response = requests.post(TOPK_JOURNALS_API, json=payload)
    response.raise_for_status()
    return response.json()  # should return list of journal IDs

def get_journal_summaries(user_id: str, journal_ids: list):
    payload = {"user_id": user_id, "journal_ids": journal_ids}
    response = requests.post(JOURNAL_SUMMARIES_API, json=payload)
    response.raise_for_status()
    return response.json()  # list of summaries

def get_user_context(user_id: str, query: str):
    """
    Fetch persona + top-k journal summaries relevant to the current query.
    """
    persona = get_persona(user_id)
    journal_ids = get_topk_journal_ids(user_id, query)
    summaries = get_journal_summaries(user_id, journal_ids)
    return persona, summaries
