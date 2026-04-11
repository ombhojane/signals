"""
Chat Router - Endpoints for chat completion.
"""

from fastapi import APIRouter, HTTPException
from services.deepseek import get_deepseek_completion
from models.schemas import ChatRequest


router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """Chat completion endpoint using Groq LLM."""
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        response = await get_deepseek_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
