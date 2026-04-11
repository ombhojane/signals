"""
LLM Provider Service - Chat completion using Groq.
"""

import os
from groq import Groq
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
