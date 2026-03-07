import json
import os
import zipfile

# ── Intent Data ───────────────────────────────────────────
intents = [
    {
        "name": "school-info",
        "phrases": [
            "Tell me about the school",
            "What is TGGHS?",
            "What is Graceful Grammar School?",
            "How old is the school?",
            "Tell me about Graceful Grammar"
        ],
        "response": "The Graceful Grammar Higher Secondary School (TGGHS) is a prestigious school in Saeedabad, Baldia Town, Karachi with 25 years of excellence! We have multiple campuses serving students from Montessori to O/A Levels."
    },
    {
        "name": "school-hours",
        "phrases": [
            "What are school hours?",
            "When does school start?",
            "What time does school end?",
            "When do classes begin?",
            "What are the timings?"
        ],
        "response": "School timings are 7:30 AM to 1:30 PM, Monday to Saturday."
    },
    {
        "name": "contact-office",
        "phrases": [
            "What is the school contact?",
            "How do I contact TGGHS?",
            "What is the school phone number?",
            "What is the school email?",
            "What is the school website?"
        ],
        "response": "You can contact TGGHS at:\n📧 Email: gracefulgrammar25@hotmail.com\n🌐 Website: www.tgghs.com\n📞 Campus I: 021-32810282\n📞 Campus II: 021-32891318\n📞 O Level Campus III: 021-32817376\n📞 Campus IV: 021-32891161\n📞 Campus V: 021-32810001-02"
    },
    {
        "name": "campus-locations",
        "phrases": [
            "Where is the school located?",
            "What are the campus addresses?",
            "Where is TGGHS?",
            "How many campuses are there?",
            "Where is Campus III?"
        ],
        "response": "TGGHS has 6 campuses in Karachi:\n🏫 Campus I: Plot 239-240, Sector-5-J, Saeedabad Baldia Town\n🏫 Campus II: Plot 249-250, Sec-5-J, Saeedabad Baldia Town\n🏫 O Level Campus III: Sec-4-A, ST-18, Saeedabad Baldia Town\n🏫 Campus IV: Tipu Sultan Road, Chandni Chowk\n🏫 Campus V: Plot 24-25, Sector 9C, New Saeedabad\n🏫 Naval Campus: St 20, Gulshan-e-Mazdoor\n🏫 Montessori Campus: 5J, Saeedabad Baldia Town"
    },
    {
        "name": "exam-boards",
        "phrases": [
            "Which board does TGGHS follow?",
            "What exam board is the school affiliated with?",
            "Does school offer O Levels?",
            "Is TGGHS affiliated with BISE?",
            "What boards are available?"
        ],
        "response": "TGGHS is affiliated with multiple exam boards:\n📚 BISE Karachi (Matric/SSC)\n📚 O Levels & A Levels\n📚 AKUEB (Aga Khan University Examination Board)\nStudents can choose the board that suits them best!"
    },
    {
        "name": "school-management",
        "phrases": [
            "Who is the director of TGGHS?",
            "Who runs the school?",
            "Who is the principal?",
            "Who founded the school?",
            "Who is in charge of the school?"
        ],
        "response": "TGGHS is led by:\n👨‍💼 Owner: Sir Muhammad Saleem\n👩‍💼 Director: Ma'am Tubi Naz\nThe school has been serving students for 25 years with excellence!"
    },
    {
        "name": "school-events",
        "phrases": [
            "Any upcoming events?",
            "What events does TGGHS have?",
            "Is there a prize distribution?",
            "When is sports day?",
            "What activities does the school organize?"
        ],
        "response": "TGGHS organizes exciting annual events including:\n🏆 Annual Prize Distribution Ceremony\n⚽ Sports Day\n🎭 Cultural Events & Competitions\n📢 Parent Teacher Meetings\nStay tuned to school notices for exact dates!"
    },
    {
        "name": "transport",
        "phrases": [
            "Does school provide transport?",
            "Is there a school bus?",
            "How do I get to school?",
            "Does TGGHS have vans?",
            "What about school transport?"
        ],
        "response": "TGGHS does not provide school transport. Students are responsible for their own commute. For directions to your nearest campus, please contact 021-32810282."
    },
    {
        "name": "admissions",
        "phrases": [
            "How do I get admission?",
            "When does admission open?",
            "How to apply to TGGHS?",
            "What is the admission process?",
            "Is admission open?"
        ],
        "response": "For admissions at TGGHS, please contact your nearest campus:\n📞 021-32810282 or 021-32891318\n📧 gracefulgrammar25@hotmail.com\n🌐 www.tgghs.com\nOur staff will guide you through the process!"
    },
    {
        "name": "school-motto",
        "phrases": [
            "What is the school motto?",
            "What does TGGHS stand for?",
            "What is the vision of the school?",
            "What makes TGGHS special?",
            "Why choose Graceful Grammar?"
        ],
        "response": "TGGHS motto is: To Which Height We Can Not Rise 🌟\nWith 25 years of excellence, TGGHS provides quality education through BISE, O/A Levels, and AKUEB — shaping the future leaders of Pakistan!"
    }
]

# ── Generate Files ────────────────────────────────────────
os.makedirs("tgghs_intents/intents", exist_ok=True)

# Agent.json — required by Dialogflow
agent_json = {
    "description": "TGGHS SchoolBot - AI Assistant for Graceful Grammar School",
    "language": "en",
    "shortDescription": "SchoolBot for TGGHS",
    "examples": "",
    "linkToDocs": "",
    "displayName": "SchoolBot",
    "unique_representation_name": "SchoolBot",
    "isPrivate": True,
    "customClassifierMode": "use.just.my.classifiers",
    "mlMinConfidence": 0.3,
    "supportedLanguages": [],
    "onePlatformApiVersion": "v2",
    "defaultTimezone": "Asia/Karachi",
    "analyzeQueryTextSentiment": False,
    "enabledKnowledgeBaseNames": [],
    "knowledgeServiceConfidenceAdjustment": -0.4,
    "dialogBuilderMode": False,
    "baseActionPackagesUrl": ""
}

with open("tgghs_intents/agent.json", "w") as f:
    json.dump(agent_json, f, indent=2)

# Package.json — also required
package_json = {"version": "1.0.0"}
with open("tgghs_intents/package.json", "w") as f:
    json.dump(package_json, f, indent=2)

for intent in intents:
    # Main intent file
    intent_json = {
        "name": intent["name"],
        "auto": True,
        "contexts": [],
        "responses": [{
            "resetContexts": False,
            "action": "",
            "affectedContexts": [],
            "parameters": [],
            "messages": [{
                "type": 0,
                "lang": "en",
                "speech": intent["response"]
            }],
            "defaultResponsePlatforms": {},
            "speech": []
        }],
        "priority": 500000,
        "webhookUsed": False,
        "webhookForSlotFilling": False,
        "fallbackIntent": False,
        "events": []
    }

    # Training phrases file
    phrases_json = [
        {
            "id": str(i),
            "data": [{"text": phrase, "userDefined": False}],
            "isTemplate": False,
            "count": 0
        }
        for i, phrase in enumerate(intent["phrases"])
    ]

    # Save files
    with open(f"tgghs_intents/intents/{intent['name']}.json", "w") as f:
        json.dump(intent_json, f, indent=2)

    with open(f"tgghs_intents/intents/{intent['name']}_usersays_en.json", "w") as f:
        json.dump(phrases_json, f, indent=2)

# ── Create ZIP ────────────────────────────────────────────
with zipfile.ZipFile("tgghs_intents.zip", "w") as zf:
    for root, dirs, files in os.walk("tgghs_intents"):
        for file in files:
            filepath = os.path.join(root, file)
            zf.write(filepath, os.path.relpath(filepath, "tgghs_intents"))

print("✅ tgghs_intents.zip created successfully!")
print("📁 Now upload this ZIP to Dialogflow!")