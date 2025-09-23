# services/metadata_extraction.py
"""
Metadata extraction using Gemini (Vertex AI Generative Model).
Extracts summary + metadata JSON from a raw journal entry.
"""

import vertexai
from vertexai.generative_models import GenerativeModel
import json
from config import PROJECT_ID, REGION

# Initialize once
vertexai.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel("gemini-2.5-flash")


def extract_metadata(journal_text: str) -> dict:
    """
    Analyze journal text -> return structured summary + metadata
    """
    prompt = f"""
You are analyzing a personal journal entry.

Journal Entry:
{journal_text}

TASK:
1. Create a concise summary (<70% length of original).
2. Extract structured metadata.

Return JSON in this format:
{{
  "summary": "short summary",
  "metadata": {{
    "date": "YYYY-MM-DD if explicitly mentioned, else null",
    "mood": "overall tone (happy, sad, anxious, calm, etc.)",
    "people": ["up to 3 important names"],
    "tags": ["main topics, themes, or activities"],
    "emotions": ["up to 3 emotions"],
    "stress_level": "low, medium, or high"
  }}
}}
"""

    response = model.generate_content(prompt)
    raw_text = response.candidates[0].content.parts[0].text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Sometimes model wraps in ```json ... ```
        cleaned = raw_text.strip("```json").strip("```").strip()
        return json.loads(cleaned)
