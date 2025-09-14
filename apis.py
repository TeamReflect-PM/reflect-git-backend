from flask import request, jsonify
from services.journal_service import analyze_store_and_embed_journal
#from services.query_service import handle_query  # assume this is in services/query_service.py

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

    # ------------------- Query Journals -------------------
    # @app.route("/query_journals", methods=["POST"])
    # def query_journals_api():
    #     try:
    #         data = request.get_json()
    #         user_id = data.get("user_id")
    #         query_text = data.get("query")
    #         top_k = data.get("top_k", 5)

    #         if not user_id or not query_text:
    #             return jsonify({"status": "error", "message": "user_id and query are required"}), 400

    #         result, status = handle_query(user_id, query_text, top_k)
    #         return jsonify(result), status

    #     except ValueError as ve:
    #         return jsonify({"status": "error", "message": str(ve)}), 400
    #     except Exception as e:
    #         print(f"Internal server error: {str(e)}")
    #         return jsonify({"status": "error", "message": "Internal server error"}), 500
