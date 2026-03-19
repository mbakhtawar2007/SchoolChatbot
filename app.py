"""
TGGHS SchoolBot — Flask Backend
================================
Handles chat requests via Google Dialogflow (primary NLP)
with a Wikipedia API fallback for unknown queries.

Author  : Muhammad Bakhtawar
School  : The Graceful Grammar Higher Secondary School, Karachi
Purpose : STEAM Competition 2026
"""

from flask import Flask, render_template, request, jsonify
import google.cloud.dialogflow as dialogflow
from google.oauth2 import service_account
import os
import uuid
import json
import re
import time
import requests

app = Flask(__name__)

# ── Configuration Constants ───────────────────────────────
PROJECT_ID       = os.environ.get("PROJECT_ID", "schoolbot-489316")
MAX_INPUT_LENGTH = 300          # chars
MIN_INPUT_LENGTH = 2            # chars
CACHE_MAX_SIZE   = 128          # max unique cached responses
CACHE_TTL        = 3600         # seconds (1 hour)
WIKI_TIMEOUT     = 8            # seconds per Wikipedia request

# Phrases that signal Dialogflow is falling back (not a real answer)
_FALLBACK_PHRASES = frozenset([
    "one more time", "sorry", "didn't get",
    "i missed that", "say that again"
])

# Wikipedia request headers (required by Wikimedia API policy)
_WIKI_HEADERS = {
    "User-Agent": "TGGHSSchoolBot/1.0 (https://school-chatbot-one.vercel.app)"
}

# ── Credentials ──────────────────────────────────────────
# On Vercel: GOOGLE_CREDENTIALS env var holds the JSON string.
# Locally  : falls back to Credentials.json file.
_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if _creds_json:
    _creds_dict  = json.loads(_creds_json)
    credentials  = service_account.Credentials.from_service_account_info(_creds_dict)
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"
    credentials = None

# ── In-Memory Response Cache ──────────────────────────────
_response_cache: dict[str, dict] = {}


def get_cached_response(key: str) -> str | None:
    """Return a cached reply if it exists and hasn't expired, else None."""
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["value"]
    return None


def set_cached_response(key: str, value: str) -> None:
    """
    Store a reply in cache.
    Evicts the oldest entry when the cache is full.
    """
    if len(_response_cache) >= CACHE_MAX_SIZE:
        oldest = min(_response_cache, key=lambda k: _response_cache[k]["ts"])
        del _response_cache[oldest]
    _response_cache[key] = {"value": value, "ts": time.time()}


# ── Input Sanitization ────────────────────────────────────
def sanitize_input(text: str) -> str:
    """
    Strip HTML tags, null bytes, and normalize whitespace.
    Returns a clean string safe to pass to external APIs.
    """
    text = re.sub(r"<[^>]+>", "", text)   # remove HTML tags
    text = text.replace("\x00", "")        # remove null bytes
    text = " ".join(text.split())          # normalize whitespace
    return text.strip()


# ── Dialogflow ────────────────────────────────────────────
def query_dialogflow(user_message: str) -> str | None:
    """
    Send the user's message to Dialogflow.

    Returns the fulfillment text if Dialogflow is confident (>50%)
    and the matched intent is not a fallback. Returns None otherwise.
    """
    try:
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session        = session_client.session_path(PROJECT_ID, str(uuid.uuid4()))

        text_input  = dialogflow.TextInput(text=user_message, language_code="en")
        query_input = dialogflow.QueryInput(text=text_input)

        response    = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        result      = response.query_result
        confidence: float = result.intent_detection_confidence
        answer: str       = result.fulfillment_text
        intent_name: str  = result.intent.display_name.lower()

        is_fallback = (
            "fallback" in intent_name
            or any(phrase in answer.lower() for phrase in _FALLBACK_PHRASES)
        )

        if confidence > 0.5 and answer and not is_fallback:
            return answer

    except Exception as exc:
        app.logger.warning("Dialogflow error: %s", exc)

    return None


# ── Wikipedia Fallback ────────────────────────────────────
def _build_short_summary(extract: str, max_sentences: int = 2) -> str:
    """Return the first `max_sentences` sentences of a Wikipedia extract."""
    sentences = extract.split(". ")
    summary   = ". ".join(sentences[:max_sentences])
    return summary if summary.endswith(".") else summary + "."


def _fetch_wiki_summary_by_title(title: str) -> str | None:
    """Fetch the Wikipedia REST summary for a given page title."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    res = requests.get(url, headers=_WIKI_HEADERS, timeout=WIKI_TIMEOUT)
    if res.status_code == 200:
        extract = res.json().get("extract", "")
        if extract:
            return f"📖 {_build_short_summary(extract)}"
    return None


def query_wikipedia(user_message: str) -> str:
    """
    Look up the user's query on Wikipedia.

    Strategy:
      1. Direct REST summary lookup (fastest path).
      2. Search API to find the best matching article title.
      3. Fetch that article's summary.
    """
    try:
        # ── Step 1: Direct lookup ──
        summary = _fetch_wiki_summary_by_title(user_message)
        if summary:
            return summary

        # ── Step 2: Search API ──
        search_params = {
            "action":   "query",
            "list":     "search",
            "srsearch": user_message,
            "format":   "json",
            "srlimit":  1,
            "utf8":     1,
        }
        search_res = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=search_params,
            headers=_WIKI_HEADERS,
            timeout=WIKI_TIMEOUT,
        )
        search_res.raise_for_status()
        results = search_res.json().get("query", {}).get("search", [])

        # ── Step 3: Fetch top result ──
        if results:
            top_title = results[0]["title"]
            summary   = _fetch_wiki_summary_by_title(top_title)
            if summary:
                return summary

    except requests.Timeout:
        app.logger.warning("Wikipedia timeout for query: %s", user_message)
        return "⏱️ The search took too long. Try a shorter question!"
    except requests.RequestException as exc:
        app.logger.error("Wikipedia request error: %s", exc)
    except Exception as exc:
        app.logger.error("Unexpected Wikipedia error: %s", exc)

    return (
        "I couldn't find information on that topic. "
        "Try rephrasing, or contact the school office for help!"
    )


# ── Routes ────────────────────────────────────────────────
@app.route("/")
def home():
    """Serve the chat UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat — process a chat message.

    Request body (JSON):
        { "message": "<user text>" }

    Response (JSON):
        { "reply": "<bot text>" }
    """
    # ── Parse request ──
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({"reply": "Invalid request format."}), 400

    raw_message: str = str(payload.get("message", "")).strip()

    # ── Validate input ──
    if not raw_message:
        return jsonify({"reply": "Please type a question first! 😊"})
    if len(raw_message) < MIN_INPUT_LENGTH:
        return jsonify({"reply": "Your message is too short. Could you be more specific?"})
    if len(raw_message) > MAX_INPUT_LENGTH:
        return jsonify({
            "reply": f"Message too long! Please keep it under {MAX_INPUT_LENGTH} characters."
        })

    # ── Sanitize ──
    user_message = sanitize_input(raw_message)

    # ── Cache lookup (case-insensitive) ──
    cache_key = user_message.lower()
    cached_reply = get_cached_response(cache_key)
    if cached_reply:
        return jsonify({"reply": cached_reply})

    # ── Generate reply ──
    try:
        bot_reply = query_dialogflow(user_message) or query_wikipedia(user_message)
    except Exception as exc:
        app.logger.error("Chat handler error: %s", exc)
        bot_reply = "Something went wrong on our end. Please try again in a moment!"

    # ── Cache and return ──
    set_cached_response(cache_key, bot_reply)
    return jsonify({"reply": bot_reply})


# ── Entry Point ───────────────────────────────────────────
if __name__ == "__main__":
    print("SchoolBot running → http://127.0.0.1:5000")
    app.run(debug=True)