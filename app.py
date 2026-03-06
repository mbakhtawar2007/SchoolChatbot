from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
from google.oauth2 import service_account
import google.generativeai as genai
import os
import uuid
import json

app = Flask(__name__)

# ── Credentials ──────────────────────────────────────────
PROJECT_ID = os.environ.get("PROJECT_ID", "schoolbot-489316")

creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if creds_json:
    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"
    credentials = None

# ── Gemini Setup ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyANCFDuGNn4SotBxNbiY6qA5WXiLJ4cb88")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ── Dialogflow ────────────────────────────────────────────
def ask_dialogflow(user_message):
    """Try to get answer from Dialogflow first."""
    session_client = dialogflow.SessionsClient(credentials=credentials)
    session_id = str(uuid.uuid4())
    session = session_client.session_path(PROJECT_ID, session_id)

    text_input = dialogflow.TextInput(text=user_message, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    confidence = response.query_result.intent_detection_confidence
    answer = response.query_result.fulfillment_text

    # Only return if confident enough (above 50%)
    if confidence > 0.5 and answer:
        return answer
    return None

# ── Gemini Fallback ───────────────────────────────────────
def ask_gemini(user_message):
    """Fallback to Gemini if Dialogflow has no answer."""
    prompt = f"""You are SchoolBot, a helpful AI assistant for a school.
Answer this student's question briefly and clearly in 2-3 sentences.
If it's not school-related, politely redirect them to ask school questions.

Student question: {user_message}"""

    response = gemini_model.generate_content(prompt)
    return response.text

# ── Routes ────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    if not user_msg:
        return jsonify({"reply": "Please type something!"})

    try:
        # Try Dialogflow first
        bot_reply = ask_dialogflow(user_msg)

        # If Dialogflow doesn't know → use Gemini
        if not bot_reply:
            bot_reply = ask_gemini(user_msg)
            bot_reply = "🤖 " + bot_reply  # mark Gemini replies with robot emoji

    except Exception as e:
        bot_reply = f"Connection error: {str(e)}"

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    print("SchoolBot is running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)