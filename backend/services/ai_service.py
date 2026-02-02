import os
import json
from groq import Groq

# --- CONFIGURATION ---

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=api_key)

# --- PROMPTS ---

# PROMPT 1: DATA EXTRACTION (The Brain)
EXTRACT_PROMPT = """
You are a medical data extractor. Your ONLY job is to update the list of symptoms based on the user's latest message.

CURRENT STATE:
{current_state}

USER MESSAGE:
"{user_message}"

RULES:
1. If the user mentions a NEW symptom, add it to the list with null details.
2. If the user provides details, update the specific field for the relevant symptom.
3. HANDLING NUMBERS: If user says "5" or "8/10", set severity="5/10".
4. MAP VAGUE INPUTS: "Hurts a lot" -> severity="Severe".
5. DO NOT change the name of an existing symptom.
6. If the user says "Yes" (to having more symptoms) but doesn't name it, DO NOT change the list.

OUTPUT JSON ONLY:
{{
  "symptoms": [
    {{ "symptom": "nausea", "severity": "mild", "duration": null, "frequency": null }}
  ]
}}
"""

# PROMPT 2: CONVERSATION (The Voice)
# ✅ FIX: Added {current_data} so the AI always sees the full list.
CONVERSATION_PROMPT = """
You are a medical triage assistant talking to a patient.

GOAL: {goal_instruction}

CURRENT COLLECTED DATA:
{current_data}

HISTORY:
{chat_history}

INSTRUCTIONS:
1. Achieve the GOAL efficiently.
2. Be polite but direct.
3. Use the exact symptom name provided in the GOAL.
4. When summarizing, READ FROM "CURRENT COLLECTED DATA" to ensure you include ALL symptoms, not just recent ones.

Generate a short, clear text reply.
"""

# --- MAIN LOGIC ---

def generate_ai_response(chat_history: list[dict], current_state: dict = None) -> dict:
    client = get_groq_client()
    user_message = chat_history[-1]["content"].strip()

    # --- STEP 1: EXTRACT DATA (The Brain) ---
    if not current_state:
        current_state = {"symptoms": []}

    extract_messages = [
        {"role": "system", "content": EXTRACT_PROMPT.format(
            current_state=json.dumps(current_state),
            user_message=user_message
        )}
    ]

    try:
        extract_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=extract_messages,
            temperature=0,
            response_format={"type": "json_object"}
        )
        new_state = json.loads(extract_res.choices[0].message.content)
    except Exception as e:
        print(f"Extraction Failed: {e}")
        new_state = current_state

    # --- STEP 2: DETERMINE NEXT MOVE (The Logic) ---

    goal = ""
    symptoms = new_state.get("symptoms", [])

    # Check for "Summary" request
    if "summary" in user_message.lower():
        goal = "The user asked for a summary. List ALL collected symptoms from the data with their details. Then ask if the information is correct."

    # Check for simple "Yes"
    elif "yes" in user_message.lower() and len(user_message) < 10:
        goal = "The user said 'Yes' to having another symptom. Ask them specifically to name the new symptom."

    else:
        missing_info_found = False

        # Check for unnamed symptoms
        for s in symptoms:
            name = s.get("symptom")
            if not name or name.lower() in ["yes", "no", "other", "symptom"]:
                goal = "The user indicated a new symptom but didn't name it. Ask them specifically what the symptom is."
                missing_info_found = True
                break

        # Check for missing fields (Reverse order)
        if not missing_info_found:
            for s in reversed(symptoms):
                name = s.get("symptom")

                if not s.get("severity"):
                    goal = f"Ask how severe the {name} is (accept 1-10 scale)."
                    missing_info_found = True
                    break
                if not s.get("duration"):
                    goal = f"Ask how long they have had the {name}."
                    missing_info_found = True
                    break
                if not s.get("frequency"):
                    goal = f"Ask how often the {name} happens."
                    missing_info_found = True
                    break

            if not missing_info_found:
                if len(symptoms) == 0:
                    goal = "Ask the user what their main symptom is today."
                else:
                    if "no" in user_message.lower() and len(user_message) < 15:
                        goal = "Thank the user, summarize ALL collected symptoms (Headache, Cough, etc.), and say goodbye."
                    else:
                        goal = "Ask if they have any OTHER symptoms they want to mention."

    # --- STEP 3: GENERATE REPLY (The Voice) ---

    msg_history_formatted = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-4:]])

    # ✅ FIX: Pass the new_state JSON into the prompt
    talk_messages = [
        {"role": "system", "content": CONVERSATION_PROMPT.format(
            goal_instruction=goal,
            current_data=json.dumps(new_state, indent=2),
            chat_history=msg_history_formatted
        )}
    ]

    reply_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=talk_messages,
        temperature=0.6
    )

    bot_reply = reply_res.choices[0].message.content.strip().replace('"', '')

    return {
        "reply": bot_reply,
        "off_topic": False,
        "extracted": new_state
    }