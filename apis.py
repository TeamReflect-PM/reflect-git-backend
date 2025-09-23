from flask import request, jsonify
from services import prompt_service, context_service, journal_service, conversation_service


#from services.query_service import handle_query  # assume this is in services/query_service.py
from services.journal_service import analyze_store_and_embed_journal

from services.persona_entry import store_persona_entry
from services.hybrid_search import hybrid_search
from services.create_embedding import get_embedding
from services.metadata_extraction import extract_metadata


def register_routes(app):

    # ------------------- Store Journal -------------------
    @app.route("/store_journal", methods=["POST"])
    def store_journal_api():
        try:
            data = request.get_json()
            status = analyze_store_and_embed_journal(data)
            if status[1] == 200:
                return jsonify({"status": "success", "message": "Journal saved successfully"}), 200
            else:
                return jsonify({"status": "error", "message": status[0].get('error')}), status[1]

        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500


    # ------------------- Therapist Chat -------------------
    @app.route("/therapist", methods=["POST"])
    def therapist_api():
        try:
            data = request.get_json()
            print("DEBUG: Incoming JSON:", data)  # 👈 Add debug

            user_id = data.get("user_id")
            query = data.get("query")

            if not user_id or not query:
                return jsonify({"status": "error", "message": "user_id and query are required"}), 400

            # --- Fetch user context (persona + journal summaries) ---
            #persona, journal_summaries = context_service.get_user_context(user_id, query)
            conversation_summaries = conversation_service.get_latest_n_summaries(user_id, n=3)

            # ---- Static test data ----
            persona = {
                "name": "Nitya",
                "traits": ["introverted", "reflective", "curious"],
                "goals": ["manage stress", "improve confidence", "balance work and life"]
            }

            journal_summaries = [
                {
                    "journal_id": "jid123",
                    "summary": "Had a stressful meeting with manager, felt anxious about deadlines.",
                    "metadata": {
                        "date": "2025-09-10",
                        "mood": "anxious",
                        "people": ["manager"],
                        "topics": ["work", "deadlines"],
                        "emotions": ["anxiety", "stress"],
                        "activities": ["meeting"],
                        "stress_level": "high"
                    }
                },
                {
                    "journal_id": "jid124",
                    "summary": "Went for a long walk, felt more calm afterwards.",
                    "metadata": {
                        "date": "2025-09-11",
                        "mood": "calm",
                        "activities": ["walking"],
                        "emotions": ["relief", "peace"],
                        "stress_level": "low"
                    }
                }
            ]

            # --- Construct prompt ---
            prompt = prompt_service.construct_prompt(query, persona, journal_summaries, conversation_summaries)

            print("prompt provided to gemini: ",prompt)


            # --- Call Gemini 2.5 Flash ---
            answer = prompt_service.call_gemini(prompt)

            #summarize and store the response
            summary_id = conversation_service.summarize_and_store_conversation(user_id, query, answer)

            return jsonify({
                "status": "success",
                "response": answer,
                "prompt_used": prompt
            }), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    # ------------------- Query Journals -------------------
    # @app.route("/query_journals", methods=["POST"])
    # def query_journals_api():
    #     try:
    #         data = request.get_json()
    #         user_id = data.get("user_id")
    #         query_text = data.get("query")
    #         top_k = data.get("top_k", 5)
    # ------------------- Store Persona -------------------
    @app.route("/store_persona", methods=["POST"])
    def store_persona_api():
        try:
            data = request.get_json()
            status = store_persona_entry(data)
            if status[1] == 200:
                return jsonify({"status": "success", "message": "Persona saved successfully"}), 200
            else:
                return jsonify({"status": "error", "message": status[0].get('error')}), status[1]

        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

# ------------------- Get Persona by User ID -------------------
    @app.route("/get_persona", methods=["GET"])
    def get_persona_api():
        try:
            user_id = request.args.get("user_id")
            
            if not user_id:
                return jsonify({"status": "error", "message": "user_id is required"}), 400

            from services.persona_entry import get_persona_by_user_id
            persona_data = get_persona_by_user_id(user_id)
            
            if persona_data:
                return jsonify({"status": "success", "data": persona_data}), 200
            else:
                return jsonify({"status": "error", "message": "Persona not found"}), 404

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    # ------------------- Get Summary+Metadata by User ID and Journal IDs -------------------
    @app.route("/get_journals_summary", methods=["GET"])
    def get_journals_summary_api():
        try:
            user_id = request.args.get("user_id")
            journal_ids = request.args.get("journal_ids")
            
            if not user_id or not journal_ids:
                return jsonify({"status": "error", "message": "user_id and journal_ids are required"}), 400

            # Parse journal_ids (comma-separated or single ID)
            if "," in journal_ids:
                journal_id_list = [jid.strip() for jid in journal_ids.split(",")]
            else:
                journal_id_list = [journal_ids.strip()]
            
            from services.journal_service import get_journals_summary_by_ids
            summary_data = get_journals_summary_by_ids(user_id, journal_id_list)
            
            return jsonify({"status": "success", "data": summary_data}), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
            
    # ------------------- Hybrid Search -------------------
    @app.route("/search_journal", methods=["POST"])
    def search_journal_api():
        try:
            data = request.get_json()
            user_id = data.get("user_id")
            query = data.get("query")
            top_k = data.get("top_k", 5)

            if not user_id or not query:
                return jsonify({"status": "error", "message": "user_id and query are required"}), 400

            # Step 1: Convert query to embedding
            query_embedding = get_embedding(query)

            # Step 2: Extract metadata from query
            metadata_filters = extract_metadata(query)

            # Step 3: Hybrid search
            results = hybrid_search(
                user_id=user_id,
                query_embedding=query_embedding,
                metadata_filters=metadata_filters,
                top_k=top_k
            )

            return jsonify({
                "status": "success",
                "results": results
            }), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
