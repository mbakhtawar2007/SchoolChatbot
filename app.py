from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
from google.oauth2 import service_account
import os
import uuid
import json

app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID", "schoolbot-489316")

# Load credentials from environment variable (for deployment)
# or from local JSON file (for local development)
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if creds_json:
    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"
    credentials = None

def ask_schoolbot(user_message):
    """Send a message to Dialogflow and get a response."""
    session_client = dialogflow.SessionsClient(credentials=credentials)
    session_id = str(uuid.uuid4())  # unique session for each conversation
    session = session_client.session_path(PROJECT_ID, session_id)

    text_input = dialogflow.TextInput(text=user_message, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    if not user_msg:
        return jsonify({"reply": "Please type something!"})
    
    try:
        bot_reply = ask_schoolbot(user_msg)
        if not bot_reply:
            bot_reply = "I'm not sure about that yet. Please ask the school office!"
    except Exception as e:
        bot_reply = f"Connection error: {str(e)}"
    
    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    print("SchoolBot is running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)