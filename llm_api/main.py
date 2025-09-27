from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from services import stt_service, llm_service, tts_service
import logging
import traceback
import os
    import uvicorn

app = FastAPI(title="Language Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextRequest(BaseModel):
    text: str
    language: Optional[str] = None

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    voice: Optional[str] = "Laura"  # Provide a default voice

@app.get("/")
async def root():
    return {"message": "Language Assistant API"}

@app.post("/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text"""
    try:
        audio_data = await audio_file.read()
        result, language_code = stt_service.stt(audio_data)
        return {"text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        logger.info(f"Received TTS request: text='{request.text}', language='{request.language}', voice='{request.voice}'")
        
        # Validate text is not empty
        if not request.text or request.text.strip() == "":
            logger.error("TTS request has empty text")
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Call TTS service with simplified error handling
        audio_data = tts_service.tts(text=request.text.strip())

        if not audio_data:
            raise HTTPException(status_code=500, detail="TTS service failed to generate audio")

        # If it's a path (string), load bytes
        if isinstance(audio_data, str):
            if os.path.exists(audio_data):
                try:
                    with open(audio_data, 'rb') as f:
                        file_bytes = f.read()
                finally:
                    # Optional: cleanup temp file
                    try:
                        os.remove(audio_data)
                    except OSError:
                        pass
                audio_data = file_bytes
            else:
                # Not a path -> maybe base64 string
                try:
                    import base64
                    audio_data = base64.b64decode(audio_data)
                except Exception:
                    raise HTTPException(status_code=500, detail="TTS service returned invalid string (not file path or base64)")

        if not isinstance(audio_data, bytes):
            raise HTTPException(status_code=500, detail=f"TTS service returned invalid audio format: {type(audio_data)}")

        # We know ElevenLabs produced MP3 (Accept: audio/mpeg). Use correct media type.
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        logger.error(f"TTS error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS service error: {str(e)}")

@app.post("/llm")
async def language_model(request: LLMRequest):
    """Process text with language model"""
    try:
        logger.info(f"Received LLM request: {request}")
        logger.info(f"LLM prompt: '{request.prompt}', max_tokens: {request.max_tokens}, temp: {request.temperature}")
        
        result = llm_service.swisscom_generate(
            messages=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        logger.info(f"LLM service returned: {result[:100]}..." if len(str(result)) > 100 else f"LLM service returned: {result}")
        
        return {"response": result}
    except Exception as e:
        logger.error(f"LLM error: {str(e)}")
        logger.error(f"LLM error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

@app.post("/conversation")
async def full_conversation(audio_file: UploadFile = File(...), language: Optional[str] = "en"):
    """Complete conversation flow: STT -> LLM -> TTS"""
    try:
        # Speech to text
        audio_data = await audio_file.read()
        user_text = stt_service.stt(audio_data)
        
        # Language model processing
        llm_response = llm_service.swisscom_generate(messages=user_text)        
        # Text to speech
        response_audio = tts_service.tts(text=llm_response)
        
        return {
            "user_input": user_text,
            "ai_response": llm_response,
            "audio_response": StreamingResponse(
                io.BytesIO(response_audio),
                media_type="audio/wav"
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add a test endpoint to check TTS service directly
@app.post("/test-tts")
async def test_tts_service():
    """Test endpoint to check what TTS service returns"""
    try:
        test_text = "Hello, this is a test"
        logger.info(f"Testing TTS service with text: '{test_text}'")
        
        result = tts_service.tts(text=test_text)
        
        return {
            "tts_result_type": str(type(result)),
            "tts_result_length": len(result) if result else 0,
            "tts_result_sample": str(result)[:200] if result else "None",
            "is_bytes": isinstance(result, bytes),
            "is_string": isinstance(result, str),
            "is_none": result is None
        }
    except Exception as e:
        logger.error(f"Test TTS error: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)