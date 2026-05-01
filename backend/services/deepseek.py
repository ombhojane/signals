"""
LLM Provider Service - Chat completion using Groq.
"""

import os
from groq import Groq
from typing import List, Dict, Any, Optional
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Lazy-load the client to avoid initialization errors if API key is not set
_client: Optional[Groq] = None

def get_client() -> Groq:
    """Get or create the Groq client (lazy initialization)."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set. "
                "Please set it before making API calls."
            )
        _client = Groq(api_key=api_key)
    return _client

async def get_deepseek_completion(messages: List[Dict[str, str]], temperature: float = 1, max_tokens: int = 1024) -> str:
    """
    Get completion from Deepseek model
    
    Args:
        messages: List of message dictionaries with role and content
        temperature: Temperature for response generation (0-1)
        max_tokens: Maximum tokens in response
        
    Returns:
        str: Generated response text
    """
    client = get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
        stream=True,
        stop=None
    )
    
    response_text = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            response_text += chunk.choices[0].delta.content
            
    return response_text
