# ==============================================================
# Reflect Project - Setup & Deployment Guide
# ==============================================================

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
