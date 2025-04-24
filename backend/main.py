from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import io
import tempfile
import time

from functions.text_to_speech import convert_text_to_speech
from functions.requests import convert_audio_to_text, translate_text_to_nepali, generate_llama_response
from functions.translation import translate_text_to_hindi
from functions.database import store_messages, reset_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_STORAGE = {}

def cleanup_audio_storage():
    """Removes old audio files from storage after 1 hour."""
    keys_to_delete = [key for key, value in AUDIO_STORAGE.items() if time.time() - value["timestamp"] > 3600]
    for key in keys_to_delete:
        del AUDIO_STORAGE[key]
    if keys_to_delete:
        logger.info(f"Cleaned up {len(keys_to_delete)} old audio files.")

@app.get("/reset")
async def reset_conversation():
    reset_messages()
    return {"response": "Conversation reset successfully"}

@app.post("/post-audio/")
async def post_audio(file: UploadFile = File(...), language: str = "hindi"):
    try:
        if not file.filename.endswith((".wav", ".mp3", ".ogg", ".flac")):
            raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")

        logger.info(f"Received file: {file.filename}")

        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_file:
            temp_file.write(file.file.read())
            temp_file.seek(0)

            message_decoded = convert_audio_to_text(temp_file)
        
        if not message_decoded:
            logger.error("1. Failed to decode audio.")
            return JSONResponse(status_code=400, content={"detail": "Failed to decode audio"})

        logger.info(f"Decoded Message: {message_decoded}")

        english_response = generate_llama_response(message_decoded)
        if not english_response:
            raise HTTPException(status_code=400, detail="Failed to generate English response")

        logger.info(f"English Response: {english_response}")

        if language == "nepali":
            translation = translate_text_to_nepali(message_decoded)
        else:
            translation = translate_text_to_hindi(message_decoded)

        if not translation:
            raise HTTPException(status_code=400, detail="Failed to generate translation")

        logger.info(f"Translation: {translation}")

        store_messages(message_decoded, english_response, translation)

        audio_output = convert_text_to_speech(translation)
        if not audio_output:
            raise HTTPException(status_code=400, detail="Failed to generate audio output")

        audio_id = f"audio_{len(AUDIO_STORAGE) + 1}"
        AUDIO_STORAGE[audio_id] = {"audio": audio_output, "timestamp": time.time()}

        return JSONResponse(content={
            "message_decoded": message_decoded,
            "english_response": english_response,
            "hindi_translation": translation if language == "hindi" else None,
            "nepali_translation": translation if language == "nepali" else None,
            "audio_id": audio_id  
        })

    except HTTPException as e:
        logger.error(f"Client error in /post-audio/: {e.detail}")
        raise e 

    except Exception as e:
        logger.error(f"Unexpected error in /post-audio/: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/get-audio/{audio_id}")
async def get_audio(audio_id: str):
    cleanup_audio_storage()
    audio_entry = AUDIO_STORAGE.get(audio_id)

    if not audio_entry:
        raise HTTPException(status_code=404, detail="Audio not found")

    return StreamingResponse(io.BytesIO(audio_entry["audio"]), media_type="audio/mpeg")

