# prompt_service.py
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import json
from config import PROJECT_ID, REGION  # Config file for project settings


# Initialize VertexAI + Firestore
vertexai.init(project=PROJECT_ID, location=REGION)

# Load Gemini 2.5 Flash
MODEL = GenerativeModel("gemini-2.5-flash")

SYSTEM_INSTRUCTIONS = """
You are an AI therapist. 
Your role is to engage in empathetic, supportive, and reflective conversations with the user. 
Always maintain a warm, non-judgmental tone.

You will receive:
1. USER PERSONA → a structured description of the user's preferences, traits, and background.  
2. CONTEXT FROM JOURNAL ENTRIES → a list of the top-k most relevant journal summaries and their metadata, 
   which may include dates, moods, people, topics, emotions, activities, and stress levels.  
3. RECENT CONVERSATION SUMMARIES → the latest N conversation summaries with metadata, user messages, and AI responses.


Guidelines:
 - Act as if you already know this user based on their persona, journal history, and recent conversation summaries.
 - Integrate the metadata naturally (e.g., noticing emotions, activities, or recurring themes) from both journals and conversation history.
 - Use the top-k journals and latest N conversation summaries as background context. They represent the most relevant past reflections and interactions.
 - Be supportive and help the user explore their thoughts and emotions, without giving generic or surface-level replies.
 - Do not repeat text directly from the persona, journals, or conversation summaries. Instead, interpret and reflect.
 - Keep answers concise but thoughtful (3–6 sentences).
 - End your reply with a gentle, open-ended follow-up question to encourage further conversation.
"""

def construct_prompt(query: str, persona: dict, journal_summaries: list, conversation_summaries: list):
    """
    Constructs the full prompt for the LLM including system instructions, persona, journal summaries, latest N conversation summaries and user query.
    """
    prompt = f"""
System Instructions:
{SYSTEM_INSTRUCTIONS}

User Persona:
{json.dumps(persona, indent=2)}

Relevant Journals:
{json.dumps(journal_summaries, indent=2)}

Recent Conversation Summaries:
{json.dumps(conversation_summaries, indent=2)}

User Query:
{query}

TASK:
Provide a thoughtful, empathetic response that:
- Acknowledges the user’s current emotions and situation.
- Integrates relevant insights from the persona and top-k journal metadata naturally.
- Offers supportive perspective or suggestions (not clinical advice).
- Keeps the reply concise but meaningful (3–6 sentences).
- You may reference relevant past conversations where appropriate.
- Ends with a gentle, open-ended question that encourages further reflection.
"""
    return prompt

def call_gemini(prompt: str):
    """
    Calls Gemini 2.5 Flash model using Vertex AI SDK.
    """
    response = MODEL.generate_content(prompt)
    return response.candidates[0].content.parts[0].text
