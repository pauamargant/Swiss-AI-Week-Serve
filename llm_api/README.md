# Language Assistant API - Hackathon Submission

A FastAPI-based web application that provides Speech-to-Text (STT), Text-to-Speech (TTS), and Large Language Model (LLM) services through REST endpoints.

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.13 or higher
- Windows PowerShell (for Windows users)

### Step 1: Clone and Navigate to Project
```bash
git clone <repository-url>
cd AI-Swiss\lang-assist
```

### Step 2: Set Up Environment Variables
1. Copy the environment template:
   ```bash
   copy .env.template .env
   ```
2. Edit the `.env` file and add your API keys:
   - **ELEVENLABS_API_KEY**: Your ElevenLabs API key for STT/TTS services
   - **APERTUS_API_KEY**: Your Apertus API key for LLM services

### Step 3: Install Dependencies
Using uv (recommended):
```bash
pip install uv
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python main.py
```

The API server will start on `http://localhost:8000`

### Step 5: Test the API
- **API Documentation**: Visit `http://localhost:8000/docs` for interactive Swagger documentation
- **Health Check**: Visit `http://localhost:8000` to verify the service is running

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check endpoint |
| `/stt` | POST | Convert audio to text |
| `/tts` | POST | Convert text to audio |
| `/llm` | POST | Process text with language model |
