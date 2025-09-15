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

#gcloud components install cloud_sql_proxy

#./cloud_sql_proxy -instances=reflect-466215:us-central1:journal-postgres=tcp:5432

#curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
#--------------------------------------------------------------------
#gcloud sql connect journal-postgres --user=postgres --database=reflect_db

#psql "host=127.0.0.1 dbname=reflect_db user=postgrespassword=Reflect@123 port=5432"