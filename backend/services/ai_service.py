from groq import Groq
import json
import os

def load_system_prompt():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "behaviour_prompts.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful assistant. Output JSON only."

SYSTEM_PROMPT = load_system_prompt()

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=api_key)

def build_messages(chat_history: list[dict], current_state: dict = None) -> list[dict]:
    system_content = SYSTEM_PROMPT
    if current_state:
        state_str = json.dumps(current_state, indent=2)
        system_content += f"\n\nCURRENT EXTRACTED DATA (DO NOT IGNORE):\n{state_str}\n"
        system_content += "Use this data to continue. Do not ask for info already collected."
    return [{"role": "system", "content": system_content}] + chat_history

# --- NEW HELPER FUNCTION: Generates questions if AI forgets ---
def generate_fallback_question(extracted_data):
    try:
        symptoms = extracted_data.get("symptoms", [])

        # FIND FIRST INCOMPLETE SYMPTOM
        target_index = -1
        for i, s in enumerate(symptoms):
            if not s.get("severity") or not s.get("duration") or not s.get("frequency"):
                target_index = i
                break

        # If everyone is happy, ask for more
        if target_index == -1:
            return "Do you have any other symptoms you want to mention?"

        # Otherwise, ask about the missing field for the found symptom
        current = symptoms[target_index]
        name = current.get("symptom") or "symptom"

        if not current.get("severity"):
            return f"How severe is the {name}?"
        if not current.get("duration"):
            return f"How long have you had the {name}?"
        if not current.get("frequency"):
            return f"How often does the {name} happen?"

        return "Could you tell me more about that?"

    except Exception:
        return "Could you tell me more about your symptoms?"

def generate_ai_response(chat_history: list[dict], current_state: dict = None) -> dict:
    client = get_groq_client()
    messages = build_messages(chat_history, current_state)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3
        )
        content = response.choices[0].message.content
        data = json.loads(content)

        # --- SMART REPAIR LOGIC ---

        # 1. Fix "Root Level Symptoms" bug
        if "symptoms" in data and isinstance(data["symptoms"], list):
            if "extracted" not in data:
                data["extracted"] = {"current_symptom_index": 0, "symptoms": []}

            if not data["extracted"].get("symptoms"):
                raw_symptoms = data["symptoms"]
                fixed_symptoms = []
                for item in raw_symptoms:
                    if isinstance(item, str):
                        fixed_symptoms.append({
                            "symptom": item, "severity": None, "duration": None, "frequency": None
                        })
                    elif isinstance(item, dict):
                        fixed_symptoms.append(item)
                data["extracted"]["symptoms"] = fixed_symptoms

        # 2. Ensure "extracted" structure exists
        if "extracted" not in data:
            data["extracted"] = current_state if current_state else {
                "current_symptom_index": 0,
                "symptoms": []
            }

        # 3. Ensure "off_topic" exists
        if "off_topic" not in data:
            data["off_topic"] = False

        # 4. CRITICAL FIX: Ensure "reply" exists with INTELLIGENT FALLBACK
        # Check synonyms first
        if "reply" not in data:
            if "message" in data: data["reply"] = data["message"]
            elif "response" in data: data["reply"] = data["response"]
            elif "question" in data: data["reply"] = data["question"]
            else:
                # Use our new helper function to generate the correct question
                data["reply"] = generate_fallback_question(data["extracted"])

        return data

    except json.JSONDecodeError:
        print("JSON Decode Error")
        return {
            "reply": "Sorry, I couldn't understand that clearly. Could you clarify?",
            "off_topic": False,
            "extracted": current_state if current_state else {
                "current_symptom_index": 0,
                "symptoms": []
            }
        }
    except Exception as e:
        print(f"General AI Error: {e}")
        return {
            "reply": "System error. Please try again.",
            "off_topic": False,
            "extracted": current_state if current_state else {
                "current_symptom_index": 0,
                "symptoms": []
            }
        }