import json
import logging
import vosk
import ollama
import os
import subprocess
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VOSK_MODEL_PATH = r"C:\\Users\\dell\\vosk-model-small-en-us-0.15"  # Update with your model path

def convert_to_wav(input_file_path):
    try:
        output_file = f"{uuid.uuid4().hex}.wav"
        
        subprocess.run([
            'ffmpeg', '-y', '-i', input_file_path, 
            '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', output_file
        ], check=True)

        return output_file
    except Exception as e:
        logger.error(f"Error in converting audio to WAV: {e}")
        return None

def convert_audio_to_text(audio_file):
    try:
        
        temp_filename = f"temp_{uuid.uuid4().hex}.wav"
        
        with open(temp_filename, "wb") as buffer:
            buffer.write(audio_file.read())

        file_path = convert_to_wav(temp_filename)
        if not file_path:
            logger.error("Failed to convert audio file to WAV")
            return None
        
        vosk_model = vosk.Model(VOSK_MODEL_PATH)
        recognizer = vosk.KaldiRecognizer(vosk_model, 16000)
        
        with open(file_path, "rb") as wav_file:
            data = wav_file.read()
            recognizer.AcceptWaveform(data)

        result = recognizer.Result()

        os.remove(file_path)
        os.remove(temp_filename)

        return json.loads(result)["text"]
        
    except Exception as e:
        logger.error(f"Error in audio transcription: {e}")
        return None

def generate_llama_response(english_text):
    try:
        response = ollama.chat(model="llama3", messages=[{"role": "user", "content": english_text}])
        english_response = response["message"]["content"].strip()

        return english_response

    except Exception as e:
        logger.error(f"Error in generating LLaMA response: {e}")
        return None

def translate_text_to_nepali(english_text):
    try:
        prompt = f"Translate the following English text into Nepali: '{english_text}' and return only the Nepali translation without any explanations or notes."
        response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        nepali_translation = response["message"]["content"].strip()

        if "Nepali Translation:" in nepali_translation:
            nepali_translation = nepali_translation.split("Nepali Translation:")[-1].strip()
            
        nepali_translation = nepali_translation.split("\n")[0]
        nepali_translation = nepali_translation.split("Note:")[0].strip() 

        return nepali_translation

    except Exception as e:
        logger.error(f"Error in text translation: {e}")
        return None

def translate_texts_to_hindi(english_text):
    try:
        translated_sentence = f"Translated sentence for: {english_text}"

        if "<start>" in translated_sentence:
            translated_sentence = translated_sentence.replace("<start>", "")
        if "<end>" in translated_sentence:
            translated_sentence = translated_sentence.replace("<end>", "")
        
        return translated_sentence.strip()

    except Exception as e:
        logger.error(f"Error in text translation to Hindi: {e}")
        return None

