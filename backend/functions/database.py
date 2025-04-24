import json
import os
from contextlib import suppress

DB_FILE = "conversation.json"

def get_recent_messages():

    if not os.path.exists(DB_FILE):
        return []

    with suppress(json.JSONDecodeError):
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return []

def store_messages(user_input, english_response, hindi_translation):

    messages = get_recent_messages()

    messages.append({"role": "user", "content": user_input})
    messages.append({"role": "assistant_english", "content": english_response})
    messages.append({"role": "assistant_hindi", "content": hindi_translation})

    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(messages, file, indent=4, ensure_ascii=False)

def reset_messages():

    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump([], file, indent=4)
