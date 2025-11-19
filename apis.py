from flask import request, jsonify
from services import prompt_service, journal_service, conversation_service, persona_entry, utils, user_service
from services.journal_service import analyze_store_and_embed_journal, get_all_journals_by_user

from services.persona_entry import store_persona_entry,get_persona_by_user_id
from services.hybrid_search import hybrid_search
from services.create_embedding import get_embedding
from services.metadata_extraction import extract_metadata
from services.user_service import get_or_create_user, get_user_profile, update_user_preferences
from datetime import datetime



def register_routes(app):

    # ------------------- Health Check -------------------
    @app.route("/", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "success", 
            "message": "Backend server is running!",
            "version": "1.0",
            "endpoints": [
                "/user/profile",
                "/store_journal",
                "/get_user_journals",
                "/therapist",
                "/store_persona",
                "/get_persona",
                "/persona",
                "/persona/<user_email>",
                "/search_journal"
            ]
        }), 200

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

    # ------------------- Get User Journals -------------------
    @app.route("/get_user_journals", methods=["GET"])
    def get_user_journals_api():
        """
        Get all journals for a user.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        """
        try:
            user_email = request.args.get("user_id")  # This is actually the email from Project 1
            limit = int(request.args.get("limit", 50))

            if not user_email:
                return jsonify({"status": "error", "message": "user_id (email) is required"}), 400

            # Get all journals for the user
            journals_data = get_all_journals_by_user(user_email, limit)

            return jsonify({
                "status": "success",
                "data": journals_data,
                "count": len(journals_data)
            }), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    # ------------------- Therapist Chat -------------------
    @app.route("/therapist", methods=["POST"])
    def therapist_api():
        """
        Therapist chatbot endpoint.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        Uses conversation_service.summarize_and_store_conversation() to store chat history.
        """
        try:
            data = request.get_json()
            print("DEBUG: Incoming JSON:", data)

            user_email = data.get("user_id")  # This is actually the email from Project 1
            query = data.get("query")
            top_k = data.get("top_k", 5)

            if not user_email or not query:
                return jsonify({"status": "error", "message": "user_id (email) and query are required"}), 400

            # --- Fetch user context (persona + journal summaries) ---
            # BRIDGE: conversation_service handles email -> internal_user_id conversion
            conversation_summaries = conversation_service.get_latest_n_summaries(user_email, n=3)

            print("DEBUG: fetched conversation summaries: ", conversation_summaries)

            # BRIDGE: persona_entry handles email -> internal_user_id conversion
            persona = get_persona_by_user_id(user_email)



            # Step 1: Convert query to embedding
            query_embedding = get_embedding(query)

            # Step 2: Extract metadata from query
            metadata_filters = extract_metadata(query)

            # Step 3: BRIDGE - Hybrid search handles email -> internal_user_id conversion for Firestore
            journal_ids = hybrid_search(
                user_id=user_email,
                query_embedding=query_embedding,
                metadata_filters=metadata_filters,
                top_k=top_k
            )

            journal_summaries = journal_service.fetch_summaries_and_metadata(user_email, journal_ids)

            print("DEBUG: journal summaries: ", journal_summaries)

            # --- Construct prompt ---
            prompt = prompt_service.construct_prompt(query, persona, journal_summaries, conversation_summaries)

            print("prompt provided to gemini: ",prompt)


            # --- Call Gemini 2.5 Flash ---
            answer = prompt_service.call_gemini(prompt)

            # BRIDGE: Summarize and store the conversation (email -> internal_user_id conversion handled inside)
            summary_id = conversation_service.summarize_and_store_conversation(user_email, query, answer)

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
        """
        Store persona endpoint.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        Uses persona_entry.store_persona_entry() which handles email -> internal_user_id conversion.
        """
        try:
            data = request.get_json()
            # BRIDGE: store_persona_entry handles email -> internal_user_id conversion
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

    # ------------------- Modern REST API for Persona -------------------
    @app.route("/persona", methods=["POST"])
    def create_persona_api():
        """
        Modern REST API endpoint for creating/updating persona.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        """
        try:
            data = request.get_json()
            # BRIDGE: store_persona_entry handles email -> internal_user_id conversion
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

    @app.route("/persona/<user_email>", methods=["GET"])
    def get_persona_by_email_api(user_email):
        """
        Modern REST API endpoint for getting persona by email.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        """
        try:
            if not user_email:
                return jsonify({"status": "error", "message": "user_email is required"}), 400

            # BRIDGE: get_persona_by_user_id handles email -> internal_user_id conversion
            persona_data = get_persona_by_user_id(user_email)

            if persona_data:
                return jsonify(persona_data), 200
            else:
                return jsonify({"status": "error", "message": "Persona not found"}), 404

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

# ------------------- Get Persona by User ID -------------------
    @app.route("/get_persona", methods=["GET"])
    def get_persona_api():
        """
        Get persona endpoint.
        Bridges Project 1 (auth via email) with Project 2 (storage).
        """
        try:
            user_email = request.args.get("user_id")  # This is actually the email from Project 1

            if not user_email:
                return jsonify({"status": "error", "message": "user_id (email) is required"}), 400

            # BRIDGE: get_persona_by_user_id handles email -> internal_user_id conversion
            from services.persona_entry import get_persona_by_user_id
            persona_data = get_persona_by_user_id(user_email)

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
            user_email = request.args.get("user_id")  # This is actually the email
            journal_ids = request.args.get("journal_ids")
            
            if not user_email or not journal_ids:
                return jsonify({"status": "error", "message": "user_id (email) and journal_ids are required"}), 400

            # Parse journal_ids (comma-separated or single ID)
            if "," in journal_ids:
                journal_id_list = [jid.strip() for jid in journal_ids.split(",")]
            else:
                journal_id_list = [journal_ids.strip()]
            
            from services.journal_service import get_journals_summary_by_ids
            summary_data = get_journals_summary_by_ids(user_email, journal_id_list)
            
            return jsonify({"status": "success", "data": summary_data}), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
            
    # ------------------- Hybrid Search -------------------
    @app.route("/search_journal", methods=["POST"])
    def search_journal_api():
        """
        Hybrid search endpoint for journals (vector + metadata search).
        Bridges Project 1 (auth via email) with Project 2 (storage).
        Uses hybrid_search() which handles:
        - Vector search in PostgreSQL (uses email directly)
        - Metadata search in Firestore (converts email -> internal_user_id)
        """
        try:
            data = request.get_json()
            user_email = data.get("user_id")  # This is actually the email from Project 1
            query = data.get("query")
            top_k = data.get("top_k", 5)

            if not user_email or not query:
                return jsonify({"status": "error", "message": "user_id (email) and query are required"}), 400

            # Step 1: Convert query to embedding
            query_embedding = get_embedding(query)

            # Step 2: Extract metadata from query
            metadata_filters = extract_metadata(query)

            # Step 3: BRIDGE - Hybrid search handles email -> internal_user_id conversion for Firestore
            results = hybrid_search(
                user_id=user_email,
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

    # ------------------- User Management APIs -------------------
    @app.route("/user/profile", methods=["GET"])
    def get_user_profile_api():
        """Get user profile from Project 2 database using email from Project 1"""
        try:
            user_email = request.args.get("email")
            
            if not user_email:
                return jsonify({"status": "error", "message": "email is required"}), 400

            user_profile = get_user_profile(user_email)
            
            if user_profile:
                return jsonify({"status": "success", "data": user_profile}), 200
            else:
                # User doesn't exist yet, create them
                user_profile = get_or_create_user(user_email)
                return jsonify({"status": "success", "data": user_profile, "created": True}), 200

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route("/user/preferences", methods=["PUT"])
    def update_user_preferences_api():
        """Update user preferences in Project 2 database"""
        try:
            data = request.get_json()
            user_email = data.get("email")
            preferences = data.get("preferences")
            
            if not user_email or not preferences:
                return jsonify({"status": "error", "message": "email and preferences are required"}), 400

            success = update_user_preferences(user_email, preferences)
            
            if success:
                return jsonify({"status": "success", "message": "Preferences updated successfully"}), 200
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route("/user/stats", methods=["GET"])
    def get_user_stats_api():
        """Get user statistics (journal count, conversation count, etc.)"""
        try:
            user_email = request.args.get("email")
            
            if not user_email:
                return jsonify({"status": "error", "message": "email is required"}), 400

            user_profile = get_user_profile(user_email)
            
            if user_profile:
                stats = {
                    "journal_count": user_profile.get("journal_count", 0),
                    "conversation_count": user_profile.get("conversation_count", 0),
                    "member_since": user_profile.get("created_at"),
                    "last_active": user_profile.get("last_active")
                }
                return jsonify({"status": "success", "data": stats}), 200
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404

        except Exception as e:
            print(f"Internal server error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
