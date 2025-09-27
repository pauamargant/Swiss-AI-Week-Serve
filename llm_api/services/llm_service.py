"""
Language Model service using Swisscom AI Platform
"""
import openai
from config import SWISS_AI_PLATFORM_API_KEY, SWISSCOM_BASE_URL, SWISSCOM_MODEL
import os

# Initialize OpenAI client for Swisscom API
swisscom_client = openai.OpenAI(
    api_key=SWISS_AI_PLATFORM_API_KEY,
    base_url=SWISSCOM_BASE_URL
) if SWISS_AI_PLATFORM_API_KEY else None

DB_PATH = "./fedlex_store"
OUTFILE = "output.mp3"

def check_and_create_db():
    if not os.path.exists(DB_PATH):
        os.system(f"python fedlex_build.py --out {DB_PATH} --config sources.json --overwrite")
        print("DB created.")
    else:
        print("DB exists.")
    


def swisscom_generate(messages, max_tokens=150, temperature=0.7):
    """
    Generate response using Swisscom AI Platform API with conversation history
    
    Args:
        messages: String or list of message dicts (e.g., [{"role": "user", "content": "..."}])
        max_tokens: Maximum tokens to generate
        temperature: Response creativity (0.0-1.0)
    
    Returns:
        str: Generated response text
    """
    check_and_create_db()

    # Query fedlex
    output = os.popen(f"python fedlex_query.py --store {DB_PATH} --lang en --k 2 --q \"{messages}\" --date_at 2025-09-26").read()

    # Prepare messages
    system_prompt = "You are Apertus, an AI language model created by the Swiss AI Initiative. Answer based on the provided context. If the context does not contain the answer, say 'I don't know'."
    user_prompt = f"{messages}. Context: {output}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    if not SWISS_AI_PLATFORM_API_KEY:
        return "Error: Swisscom AI Platform API key not found. Please check your .env file."
    
    if not swisscom_client:
        return "Error: Swisscom client not initialized. Please check your API key."
    
    # Convert string input to proper message format
    
    # Validate message format
    if not isinstance(messages, list) or not messages:
        return "Error: Messages must be a non-empty list or string."
    
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            return "Error: Each message must be a dict with 'role' and 'content' keys."
    
    try:
        response = swisscom_client.chat.completions.create(
            model=SWISSCOM_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
                
    except Exception as e:
        return f"LLM Error: {str(e)}"
