from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
import os
import uuid

app = Flask(__name__)

# -----------------------------------------------
# REPLACE THESE TWO VALUES WITH YOUR OWN:
# -----------------------------------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"  # your JSON file name
PROJECT_ID = "schoolbot-489316"  # paste your Project ID here
# -----------------------------------------------

def ask_schoolbot(user_message):
    """Send a message to Dialogflow and get a response."""
    session_client = dialogflow.SessionsClient()
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