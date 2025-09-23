# Reflect Project
#Activate the .venv
#python3 -m venv .venv
#source .venv/bin/activate
#deactivate
#--------------------------------------------------------------------
#Install requirements.txt
#pip install -r requirements.txt
#--------------------------------------------------------------------
#command to run the app
#python main.py
#--------------------------------------------------------------------
#command to test - change the port number
#curl -X POST http://localhost:8081/store_journal -H "Content-Type: application/json" -d @journal.json
#--------------------------------------------------------------------
#if you face gloud authentication errors
#gcloud config set project reflect-466215
#gcloud auth login
#-------------------------------------------------
#cloud proxy server

# for local testing, setup a proxy server to establish connection between cloud shell and postgres db. This will help us connecting the app to db
# curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
# chmod +x cloud_sql_proxy

#run this to start the proxy server in a new bash terminal
# ./cloud_sql_proxy -instances=reflect-466215:us-central1:journal-postgres=tcp:5432

#connect to the db to view data from terminal
#psql "host=127.0.0.1 dbname=reflect_db user=postgres password=Reflect@123 port=5432"

#give these properties in config.py
#PG_HOST = "127.0.0.1"       # your DB host/IP
#PG_DB = "reflect_db"           # your database name
#PG_USER = "postgres"       # your DB user
#PG_PASSWORD = "Reflect@123"  # your DB password
#PG_PORT = 5432                 # default PostgreSQL port

#--------------------------------------------------------------------
#gcloud sql connect journal-postgres --user=postgres --database=reflect_db

#for production, proxy server is not required as the deploy code run in the same network as db

#---------------------------------
# DB setup steps - one time(already done)
#connect to database locally from bash to view data
#psql "host=127.0.0.1 port=5432 dbname=reflect_db user=postgres password=Reflect@123"
#Inside the psql shell:
#CREATE EXTENSION IF NOT EXISTS vector;
#CREATE TABLE journal_embeddings (
    id SERIAL PRIMARY KEY,
    journal_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    embedding vector(768),  -- matches text-embedding-005 model
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(journal_id)
);

# Deploy into cloudrun service steps for production(one time env vars and secrets)
#create build
#gcloud builds submit --tag gcr.io/reflect-466215/reflect-backend:latest .
#create deploy service
#gcloud run deploy reflect-backend \
  --image=gcr.io/reflect-466215/reflect-backend:latest \
  --add-cloudsql-instances=reflect-466215:us-central1:journal-postgres \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=PG_HOST=/cloudsql/reflect-466215:us-central1:journal-postgres,PG_DB=reflect_db,PG_USER=postgres,PG_PORT=5432

#echo -n "<YOUR_DB_PASSWORD>" | gcloud secrets create pg-password --data-file=- --project=reflect-466215
#Grant Cloud Run service account access
PROJECT_NUMBER=$(gcloud projects describe reflect-466215 --format='value(projectNumber)')
SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding reflect-466215 \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding reflect-466215 \
  --member="serviceAccount:$SA" \
  --role="roles/cloudsql.client"

#Attach secret to the service
#gcloud run services update reflect-backend \
  --region=us-central1 \
  --set-secrets=PG_PASSWORD=pg-password:latest

# Conversation embeddings table
CREATE TABLE conversation_embeddings (
    id SERIAL PRIMARY KEY,
    summary_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    embedding vector(768),  -- matches text-embedding-005 model
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(summary_id)
);
