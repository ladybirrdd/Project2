import requests
from decouple import config
from requests.exceptions import RequestException, Timeout
import time

ELEVEN_LABS_API_KEY = config("ELEVEN_LABS_API_KEY")

DEFAULT_VOICE_ID = "bIHbv24MWmeRgasZH58o" 

def convert_text_to_speech(message, voice_id=DEFAULT_VOICE_ID):

    body = {
        "text": message,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.6
        }
    }

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json",
        "accept": "audio/mpeg"
    }

    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    for attempt in range(3):
        try:
            response = requests.post(endpoint, json=body, headers=headers, timeout=10)
            response.raise_for_status()
            if response.status_code == 200 and "audio/mpeg" in response.headers.get("Content-Type", ""):
                print(f"Received audio on attempt {attempt + 1}")
                return response.content
            else:
                print(f"Unexpected response: {response.status_code} - {response.text}")
                return None
        except Timeout:
            print(f"Timeout on attempt {attempt + 1}, retrying...")
        except RequestException as e:
            print(f"Request error on attempt {attempt + 1}: {e}, retrying...")

        time.sleep(3)

    print("Failed to generate audio after 3 attempts.")
    return None