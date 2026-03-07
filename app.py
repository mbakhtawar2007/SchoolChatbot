from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
from google.oauth2 import service_account
import os
import uuid
import json
import requests

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

# ── Wikipedia Fallback ────────────────────────────────────
def ask_wikipedia(user_message):
    """Search Wikipedia for an answer."""
    headers = {"User-Agent": "SchoolChatbot/1.0 (https://schoolbot.vercel.app)"}
    try:
        # Single API call — faster and more reliable
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + user_message.replace(" ", "_")
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code == 200:
            data = res.json()
            extract = data.get("extract", "")
            if extract:
                # Return first 2 sentences
                sentences = extract.split(". ")
                short = ". ".join(sentences[:2]) + "."
                return f"📖 {short}"

        # Fallback — try search API
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": user_message,
            "format": "json",
            "srlimit": 1,
            "utf8": 1
        }
        res2 = requests.get(search_url, params=params, headers=headers, timeout=10)
        data2 = res2.json()
        results = data2.get("query", {}).get("search", [])

        if results:
            title = results[0]["title"]
            res3 = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
                headers=headers, timeout=10
            )
            if res3.status_code == 200:
                extract = res3.json().get("extract", "")
                sentences = extract.split(". ")
                short = ". ".join(sentences[:2]) + "."
                return f"📖 {short}"

        return "I couldn't find information on that topic. Try rephrasing your question!"

    except Exception as e:
        print(f"Wikipedia error: {e}")  # For debugging on Vercel logs
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

    try:
        # Try Dialogflow first
        bot_reply = ask_dialogflow(user_msg)

        # If Dialogflow doesn't know → use Wikipedia
        if not bot_reply:
            bot_reply = ask_wikipedia(user_msg)

    except Exception as e:
        bot_reply = f"Connection error: {str(e)}"

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    print("SchoolBot is running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)