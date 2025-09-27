# Serva Assistant
This repository contains:
1. **LLM API Backend** - A FastAPI-based service providing Speech-to-Text, Text-to-Speech, and Language Model capabilities
2. **Web Application Frontend** - A modern React/TypeScript interface for interacting with the RAG system

## 🚀 Quick Start Guide

To run this demo, you need to set up both the backend API and the frontend web application. Follow the instructions below in order:

### Step 1: Set Up the LLM API Backend

#### Prerequisites
- Python 3.13 or higher
- Windows PowerShell (for Windows users)

#### Setup Instructions

1. **Navigate to the API directory:**
   ```bash
   cd llm_api
   ```

2. **Set up environment variables:**
   ```bash
   copy .env.template .env
   ```
   Edit the `.env` file and add your API keys:
   - **ELEVENLABS_API_KEY**: Your ElevenLabs API key for STT/TTS services
   - **APERTUS_API_KEY**: Your Apertus API key for LLM services

3. **Install dependencies:**
   Using uv (recommended):
   ```bash
   pip install uv
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the API server:**
   ```bash
     uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 
   ```

The API server will be available at `http://localhost:8000`

- **API Documentation**: Visit `http://localhost:8000/docs`
- **Health Check**: Visit `http://localhost:8000`

### Step 2: Set Up the Web Application Frontend

#### Prerequisites
- Node.js & npm - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

#### Setup Instructions

1. **Navigate to the webapp directory:**
   ```bash
   cd webapp
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

The web application will be available at `http://localhost:8080`
