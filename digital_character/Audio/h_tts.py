import http.client
import json
import os
import hashlib

CACHE_FILE = "tts_cache.json"
_memory_cache = {}

def _load_cache():
    global _memory_cache
    if not _memory_cache and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _memory_cache = json.load(f)
        except Exception:
            _memory_cache = {}

def _save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def generate_speech(text, voice="nova"):
    _load_cache()
    text_hash = hashlib.md5(f"{text}_{voice}".encode('utf-8')).hexdigest()
    filename = f"speech_{text_hash}.mp3"

    if text in _memory_cache:
        cached_filename = _memory_cache[text]
        if os.path.exists(cached_filename):
            return cached_filename
        else:
            del _memory_cache[text]

    try:
        API_KEY = "your_api"
        conn = http.client.HTTPSConnection("jmpb-szb.com")
        payload = json.dumps({"model": "gpt-4o-mini-tts", "input": text, "voice": voice})
        headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
        conn.request("POST", "/v1/audio/speech", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        with open(filename, "wb") as f:
            f.write(data)
        conn.close()
        
        _memory_cache[text] = filename
        _save_cache()
        return filename
    except Exception as e:
        print(f"语音转换失败: {e}")
        return None