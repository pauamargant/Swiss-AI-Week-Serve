"""
Configuration module for AI Language Assistant
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
SWISS_AI_PLATFORM_API_KEY = os.getenv("SWISS_AI_PLATFORM_API_KEY")

# ElevenLabs API endpoints
ELEVENLABS_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

# Swisscom API configuration
SWISSCOM_BASE_URL = "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b/v1"
SWISSCOM_MODEL = "swiss-ai/Apertus-70B"
SWISSCOM_MODEL = "swiss-ai/Apertus-70B"

