from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import io
import tempfile
import time

from functions.text_to_speech import convert_text_to_speech
from functions.requests import convert_audio_to_text, translate_text_to_nepali, generate_llama_response, translate_texts_to_hindi
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
    keys_to_delete = [key for key, value in AUDIO_STORAGE.items() if time.time() - value["timestamp"] > 3600]
    for key in keys_to_delete:
        del AUDIO_STORAGE[key]

@app.get("/reset")
async def reset_conversation():
    reset_messages()
    return {"response": "Conversation reset successfully"}

@app.post("/decode-audio/")
async def decode_audio(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith((".wav", ".mp3", ".ogg", ".flac")):
            raise HTTPException(status_code=400, detail="Invalid file type")

        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_file:
            temp_file.write(file.file.read())
            temp_file.seek(0)
            message = convert_audio_to_text(temp_file)

        if not message:
            raise HTTPException(status_code=400, detail="Failed to decode audio")

        logger.info(f"Decoded Message: {message}")
        return {"message_decoded": message}

    except Exception as e:
        logger.error(f"decode-audio error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/generate-response/")
async def generate_response(data: dict):
    try:
        message = data.get("message")
        language = data.get("language")

        if not message or language not in ["hindi", "nepali"]:
            raise HTTPException(status_code=400, detail="Invalid input")

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_llm = executor.submit(generate_llama_response, message)
            future_translation = executor.submit(
                translate_text_to_nepali if language == "nepali" else translate_text_to_hindi,
                message
            )

            english_response = future_llm.result()
            translation = future_translation.result()

        if not english_response or not translation:
            raise HTTPException(status_code=400, detail="Generation failed")

        store_messages(message, english_response, translation)

        return {
            "english_response": english_response,
            "translation": translation
        }

    except Exception as e:
        logger.error(f"generate-response error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/generate-audio/")
async def generate_audio(data: dict):
    try:
        translation = data.get("translation")
        if not translation:
            raise HTTPException(status_code=400, detail="Missing translation")

        audio = convert_text_to_speech(translation)
        if not audio:
            raise HTTPException(status_code=500, detail="TTS generation failed")

        audio_id = f"audio_{len(AUDIO_STORAGE) + 1}"
        AUDIO_STORAGE[audio_id] = {"audio": audio, "timestamp": time.time()}
        return {"audio_id": audio_id}

    except Exception as e:
        logger.error(f"generate-audio error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/get-audio/{audio_id}")
async def get_audio(audio_id: str):
    cleanup_audio_storage()
    audio_entry = AUDIO_STORAGE.get(audio_id)

    if not audio_entry:
        raise HTTPException(status_code=404, detail="Audio not found")

    return StreamingResponse(io.BytesIO(audio_entry["audio"]), media_type="audio/mpeg")
