from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
from google.oauth2 import service_account
import os
import uuid
import json
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID", "schoolbot-489316")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if creds_json:
    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"
    credentials = None

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
    intent_name = response.query_result.intent.display_name

    # Ignore default fallback intent — let Wikipedia handle it
    fallback_phrases = ["one more time", "sorry", "didn't get",
                        "i missed that", "say that again"]
    is_fallback = "fallback" in intent_name.lower() or \
                  any(p in answer.lower() for p in fallback_phrases)

    if confidence > 0.5 and answer and not is_fallback:
        return answer
    return None

# ── DuckDuckGo Fallback ───────────────────────────────────
# ── OpenRouter Fallback ───────────────────────────────────
def ask_openrouter(user_message):
    """Fallback to OpenRouter free AI if Dialogflow has no answer."""
    try:
        normalized = user_message.lower().strip()
        if normalized in ["assalam-o-alaikum", "assalam o alaikum", "assalamualaikum", "salam"]:
            return "Walikum assalam! How can I help you today? Ask me anything about TGGHS! 😊"

        greetings = ["hi", "hello", "hey", "ok", "okay", "thanks", "bye"]
        if normalized in greetings:
            return "Hello! How can I help you today? Ask me anything about TGGHS! 😊"

        # Guardrail: restrict answers to TGGHS scope only
        out_of_scope_phrases = [
            "capital of", "weather", "news", "stock", "crypto", "movie", "football", "recipe", "how to make", "politics", "government",
            "oscar", "nobel", "general knowledge", "history of", "science project", "mathematics", "math problem", "translation"
        ]
        school_context_terms = [
            "tggsh", "school", "campus", "campuses", "admission", "admissions", "exam", "exams", "board", "boards", "timing", "hours", "fee", "fees",
            "transport", "events", "management", "motto", "contact", "office", "teacher", "student", "curriculum", "teacher"
        ]

        if any(phrase in normalized for phrase in out_of_scope_phrases):
            return "I can only answer questions about The Graceful Grammar Higher Secondary School (TGGHS). Please ask about admissions, timings, campuses, boards, exams, or school services."

        if not any(term in normalized for term in school_context_terms):
            return "I can only answer questions about The Graceful Grammar Higher Secondary School (TGGHS). Please ask about admissions, timings, campuses, boards, exams, or school services."

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are SchoolBot, a helpful AI assistant for The Graceful Grammar Higher Secondary School (TGGHS) in Karachi, Pakistan. Answer student questions briefly in 2-3 sentences. Keep answers short and clear."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 150
            },
            timeout=10
        )
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        return "🤖 " + answer.strip()

    except Exception as e:
        return "I couldn't find an answer right now. Please ask the school office for help!"

# ── Routes ────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    if not user_msg:
        return jsonify({"reply": "Please type something!"})

    normalized = user_msg.lower().strip()
    greeting_responses = {
        "assalam-o-alaikum": "Walikum assalam! How can I help you today? Ask me anything about TGGHS! 😊",
        "assalam o alaikum": "Walikum assalam! How can I help you today? Ask me anything about TGGHS! 😊",
        "assalamualaikum": "Walikum assalam! How can I help you today? Ask me anything about TGGHS! 😊",
        "salam": "Walikum assalam! How can I help you today? Ask me anything about TGGHS! 😊",
        "hi": "Hello! How can I help you today? Ask me anything about TGGHS! 😊",
        "hello": "Hello! How can I help you today? Ask me anything about TGGHS! 😊",
        "hey": "Hello! How can I help you today? Ask me anything about TGGHS! 😊",
        "ok": "Hello! How can I help you today? Ask me anything about TGGHS! 😊",
        "okay": "Hello! How can I help you today? Ask me anything about TGGHS! 😊",
        "thanks": "You’re welcome! What would you like to know about TGGHS? 😊",
        "bye": "Goodbye! Feel free to ask anytime about TGGHS. 😊"
    }

    if normalized in greeting_responses:
        return jsonify({"reply": greeting_responses[normalized]})

    try:
        # Try Dialogflow first
        bot_reply = ask_dialogflow(user_msg)

        # If Dialogflow doesn't know → use OpenRouter
        if not bot_reply:
            bot_reply = ask_openrouter(user_msg)

    except Exception as e:
        bot_reply = f"Connection error: {str(e)}"

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    print("SchoolBot is running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)