

import httpx
from config import ELEVENLABS_API_KEY, ELEVENLABS_STT_URL


def stt(audio_file):
    """
    Convert audio to text using ElevenLabs Speech-to-Text API
    
    Args:
        audio_file: Path to audio file or file-like object
    
    Returns:
        tuple: (transcribed_text, language_code) or (error_message, None)
    """
    if not ELEVENLABS_API_KEY:
        return "Error: ElevenLabs API key not found. Please check your .env file.", None
    
    try:
        # Handle file input (path, file object, or raw bytes)
        if isinstance(audio_file, str):
            with open(audio_file, "rb") as f:
                audio_data = f.read()
        elif hasattr(audio_file, "read"):
            audio_data = audio_file.read()
        else:
            audio_data = audio_file

        files = {
            "file": ("audio.wav", audio_data, "audio/wav")  # must be "file"
        }
        
        data = {
            "model_id": "scribe_v1"
        }
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        with httpx.Client() as client:
            response = client.post(
                ELEVENLABS_STT_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=30.0
            )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "No text transcribed")
            language_code = result.get("language_code", None)
            return text, language_code
        else:
            return f"STT Error: {response.status_code} - {response.text}", None
    
    except Exception as e:
        return f"STT Error: {str(e)}", None
