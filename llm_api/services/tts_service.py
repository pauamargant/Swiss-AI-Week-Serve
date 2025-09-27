"""
Text-to-Speech service using ElevenLabs API
"""
import tempfile
import httpx
from config import ELEVENLABS_API_KEY, ELEVENLABS_TTS_URL, ELEVENLABS_VOICE_ID


def tts(text):
    """
    Convert text to speech using ElevenLabs Text-to-Speech API
    
    Args:
        text: Text to convert to speech
    
    Returns:
        str: Path to generated audio file
    """
    if isinstance(text, bytes):
        text = text.decode('utf-8')
   
    if not ELEVENLABS_API_KEY:
        return None
    
    try:
        with httpx.Client() as client:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = client.post(
                f"{ELEVENLABS_TTS_URL}/{ELEVENLABS_VOICE_ID}",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Create a temporary audio file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(response.content)
                    return tmp_file.name
            else:
                print(f"TTS Error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None
