# ==============================================================
# Reflect Project - Setup & Deployment Guide
# ==============================================================

# Reflect is an AI-powered mental health companion providing personalized support through journal analysis and empathetic conversation. It uses AI to understand user emotions and provide tailored guidance, building a dynamic user persona based on journal entries and onboarding information. The goal is to make mental wellness support accessible by combining AI precision with human empathy.
# Journal Functionality
# When a user creates a journal entry, the text is stored in Firestore along with metadata like timestamp, mood rating, and tags. The entry is then sent to Vertex AI's text embedding API to generate a 768-dimensional vector representation capturing its semantic meaning. This vector embedding is stored in Vertex AI Matching Engine's vector database, indexed by the user ID for fast retrieval during conversations.

# Persona Functionality
# During onboarding, users complete a questionnaire covering personality traits, mental health history, triggers, coping mechanisms, and communication preferences. These responses are structured into a comprehensive persona profile and stored in Firestore. The persona acts as the foundational context layer that shapes how the AI communicates with each user, ensuring responses match their preferred tone, address their specific concerns, and align with their therapeutic goals.

# AI Chatbot Functionality
# When a user sends a message to the AI therapist, the system first converts the message into a vector embedding using the same text embedding model. This query vector is compared against all the user's stored journal vectors using cosine similarity to find the 5-10 most emotionally and contextually relevant past entries. The system then constructs a comprehensive prompt combining the user's persona profile, retrieved journal entries, recent conversation summaries, and the current message. This enriched prompt is sent to Vertex AI's Gemini 2.5 Flash model, which generates a personalized, therapeutic response grounded in the user's actual experiences and emotional history. After each conversation, key insights and progress notes are summarized and stored to maintain continuity across sessions, ensuring the AI remembers important details and therapeutic breakthroughs over time.
# 1. User Personas
# Three diverse user profiles representing common mental health challenges: a college student with anxiety, a working professional experiencing depression and burnout, and a recent graduate processing grief. Each persona includes detailed mental health history, personality traits, coping mechanisms, and lifestyle context that the AI uses to personalize responses and recommendations.

# 2. Journal Entries
# Real-world journal entries from each user persona showing their emotional journeys over time. Entries include mood ratings, tags, contextual information, and vector embeddings for semantic search. These demonstrate how users document struggles, victories, and patterns that the AI analyzes to provide personalized support.

# 3. AI Conversation Summaries
# Therapeutic session summaries that capture key insights, emotional progress, coping strategies discussed, and follow-up needs. These summaries maintain continuity between conversations, allowing the AI to reference past breakthroughs and track long-term therapeutic progress for each user.


# -----------------------------
# 🐍 Virtual Environment Setup
# -----------------------------
# Activate the .venv
# python3 -m venv .venv
# source .venv/bin/activate
# deactivate

# -----------------------------
# 📦 Install Requirements
# -----------------------------
# pip install -r requirements.txt

# -----------------------------
# ▶️ Run the App
# -----------------------------
# python main.py

# -----------------------------
# 🧪 Local Testing (APIs)
# -----------------------------
# Command to test journal storage
# curl -X POST http://localhost:8081/store_journal -H "Content-Type: application/json" -d @journal.json

# Command to test persona entry
# curl -X POST http://localhost:8081/store_persona -H "Content-Type: application/json" -d @persona.json

# Get journal summaries
# curl -X GET http://localhost:8081/get_journals_summary?user_id=testuser-nitya&journal_ids=0c4e9b2d-5ff7-40b2-806c-3ab9ec8cc54c

# Get persona
# curl -X GET http://localhost:8081/get_persona?user_id=testuser-nitya

# -----------------------------
# 🔍 Search API (Top-K Search)
# -----------------------------
# curl -X POST http://localhost:9090/search_journal -H "Content-Type: application/json" -d @search_payload.json

# curl -X POST http://localhost:9090/therapist -H "Content-Type: application/json" -d @therapist_payload.json

# -----------------------------
# 🔑 Authentication Fix (if errors)
# -----------------------------
# gcloud config set project reflect-466215
# gcloud auth login

# -----------------------------
# 🌐 Cloud Proxy Server (Local Testing)
# -----------------------------
# For local testing, setup a proxy server to establish connection between cloud shell and postgres db.

# Download proxy
# curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
# chmod +x cloud_sql_proxy

# Run proxy (in new bash terminal)
# ./cloud_sql_proxy -instances=reflect-466215:us-central1:journal-postgres=tcp:5432

# -----------------------------
# 🗄️ Connect to Database (Local)
# -----------------------------
# Connect to DB to view data
# psql "host=127.0.0.1 dbname=reflect_db user=postgres password=Reflect@123 port=5432"

# -----------------------------
# ⚙️ Config Settings (config.py)
# -----------------------------
# PG_HOST = "127.0.0.1"          # your DB host/IP
# PG_DB = "reflect_db"           # your database name
# PG_USER = "postgres"           # your DB user
# PG_PASSWORD = "Reflect@123"    # your DB password
# PG_PORT = 5432                 # default PostgreSQL port

# -----------------------------
# 🔌 Direct Cloud SQL Connect
# -----------------------------
# gcloud sql connect journal-postgres --user=postgres --database=reflect_db

# For production, proxy server is NOT required (Cloud Run connects internally).

# -----------------------------
# 🛠️ Database Setup (One-Time)
# -----------------------------
# Connect to database locally:
# psql "host=127.0.0.1 port=5432 dbname=reflect_db user=postgres password=Reflect@123"

# Inside psql shell:
# CREATE EXTENSION IF NOT EXISTS vector;
# CREATE TABLE journal_embeddings (
#     id SERIAL PRIMARY KEY,
#     journal_id TEXT NOT NULL,
#     user_id TEXT NOT NULL,
#     embedding vector(768),  -- matches text-embedding-005 model
#     created_at TIMESTAMP DEFAULT NOW(),
#     UNIQUE(journal_id)
# );

# -----------------------------
# 🚀 Deploy to Cloud Run (Production)
# -----------------------------
# Create build
# gcloud builds submit --tag gcr.io/reflect-466215/reflect-backend:latest .

# Deploy service
# gcloud run deploy reflect-backend \
#   --image=gcr.io/reflect-466215/reflect-backend:latest \
#   --add-cloudsql-instances=reflect-466215:us-central1:journal-postgres \
#   --region=us-central1 \
#   --platform=managed \
#   --allow-unauthenticated \
#   --set-env-vars=PG_HOST=/cloudsql/reflect-466215:us-central1:journal-postgres,PG_DB=reflect_db, #  PG_USER=postgres,PG_PORT=5432

# -----------------------------
# 🔒 Secrets Setup
# -----------------------------
# echo -n "<YOUR_DB_PASSWORD>" | gcloud secrets create pg-password --data-file=- --project=reflect-466215

# -----------------------------
# 👤 IAM Permissions for Cloud Run
# -----------------------------

# PROJECT_NUMBER=$(gcloud projects describe reflect-466215 --format='value(projectNumber)')
# SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
# gcloud projects add-iam-policy-binding reflect-466215 \
#   --member="serviceAccount:$SA" \
#   --role="roles/secretmanager.secretAccessor"
# gcloud projects add-iam-policy-binding reflect-466215 \
#   --member="serviceAccount:$SA" \
#   --role="roles/cloudsql.client"

# -----------------------------
# 🔗 Attach Secret to Cloud Run Service
# -----------------------------
# gcloud run services update reflect-backend \
#   --region=us-central1 \
#   --set-secrets=PG_PASSWORD=pg-password:latest


# Conversation embeddings table
CREATE TABLE conversation_embeddings (
    id SERIAL PRIMARY KEY,
    summary_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    embedding vector(768),  -- matches text-embedding-005 model
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(summary_id)
);
