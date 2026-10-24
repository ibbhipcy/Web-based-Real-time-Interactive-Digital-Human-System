import requests
import os

def transcribe_audio(audio_filepath, language="zh"):
    if not os.path.exists(audio_filepath):
        return None

    API_KEY = "your_apikey"
    API_URL = "https://api.openai.com/v1/audio/transcriptions"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    try:
        with open(audio_filepath, "rb") as audio_file:
            files = {
                'file': (os.path.basename(audio_filepath), audio_file, 'audio/mpeg'),
                'model': (None, 'whisper-1'),
                'language': (None, language)
            }
            response = requests.post(API_URL, headers=headers, files=files)
            response.raise_for_status()
            return response.json().get("text", "").strip()
    except Exception as e:
        print(f"ASR 发生错误: {e}")
        return None