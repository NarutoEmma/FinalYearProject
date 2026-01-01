from groq import Groq
import json
import os

def get_groq_client():
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=api_key)


SYSTEM_PROMPT = """
You are a medical triage assistant.

STRICT OUTPUT RULES (NON-NEGOTIABLE):
- You MUST ONLY output valid JSON
- Do NOT include markdown
- Do NOT include explanations
- Do NOT include text outside JSON
- If you break JSON format, the response will be rejected

CONVERSATION CONTROL (MANDATORY):
- You MUST always attempt to extract information from the user's message.
- You MUST NEVER ask a generic question like "can you explain more".
- You MUST follow this strict order when asking questions:
  1. symptom
  2. severity
  3. duration
  4. frequency

QUESTION RULES:
- If symptom is null → ask what symptom they are experiencing.
- If symptom is present AND severity is null → ask about severity ONLY.
- If severity is present AND duration is null → ask about duration ONLY.
- If duration is present AND frequency is null → ask about frequency ONLY.
- If all fields are present → acknowledge and ask if anything else should be added.

FAILURE CONDITIONS:
- Asking vague questions is NOT allowed.
- Asking about multiple fields at once is NOT allowed.

EXAMPLES:

User: "I have a headache"
Assistant:
{
  "reply": "How severe is the headache (mild, moderate, severe, or 1–10)?",
  "off_topic": false,
  "extracted": {
    "symptom": "headache",
    "severity": null,
    "duration": null,
    "frequency": null
  }
}

User: "It's about a 7"
Assistant:
{
  "reply": "How long have you had this headache?",
  "off_topic": false,
  "extracted": {
    "symptom": "headache",
    "severity": "7",
    "duration": null,
    "frequency": null
  }
}

User: "Since yesterday"
Assistant:
{
  "reply": "How often does the headache occur?",
  "off_topic": false,
  "extracted": {
    "symptom": "headache",
    "severity": "7",
    "duration": "1 day",
    "frequency": null
  }
}

OUTPUT FORMAT (MUST MATCH EXACTLY):

{
  "reply": string,
  "off_topic": boolean,
  "extracted": {
    "symptom": string | null,
    "duration": string | null,
    "severity": string | null,
    "frequency": string | null
  }
}

You MUST attempt to fill extracted fields on EVERY response.
Your response will be automatically validated.
"""


def build_messages(chat_history: list[dict])-> list[dict]:
    """ chat_history =[
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}]"""
    return [{"role": "system", "content": SYSTEM_PROMPT}]+chat_history

def generate_ai_response(chat_history: list[dict])-> dict:
    client = get_groq_client()
    messages = build_messages(chat_history)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3)
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "reply": "Sorry, I couldn't understand that clearly. Could you clarify?",
            "off_topic": False,
            "extracted": {
                "symptom": None,
                "duration": None,
                "severity": None,
                "frequency": None
            }
        }
