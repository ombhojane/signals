"""
Output Parser - Extract and validate JSON from LLM responses.
"""

import re
import json
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel, ValidationError
from core.logging import logger

T = TypeVar('T', bound=BaseModel)


def extract_json_from_response(text: str) -> Optional[str]:
    """
    Extract JSON from LLM response that may contain markdown fences.
    
    Handles:
    - ```json {...} ```
    - ``` {...} ```
    - Raw JSON {...}
    """
    if not text:
        return None
    
    # Pattern 1: JSON in markdown code block ```json ... ```
    json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(json_block_pattern, text)
    if matches:
        return matches[0].strip()
    
    # Pattern 2: Raw JSON object
    json_object_pattern = r'\{[\s\S]*\}'
    matches = re.findall(json_object_pattern, text)
    if matches:
        # Return the largest match (likely the full JSON)
        return max(matches, key=len)
    
    return None


def parse_llm_response(
    response_text: str,
    model_class: Type[T],
    strict: bool = False
) -> tuple[Optional[T], Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse LLM response text into a Pydantic model.
    
    Args:
        response_text: Raw LLM response string
        model_class: Pydantic model class to validate against
        strict: If True, raise on validation error; if False, return raw dict
        
    Returns:
        Tuple of (validated_model, raw_dict, error_message)
        - validated_model: Pydantic model if validation succeeds
        - raw_dict: Parsed JSON dict (even if validation fails)
        - error_message: Error description if parsing/validation fails
    """
    # Extract JSON from response
    json_str = extract_json_from_response(response_text)
    
    if not json_str:
        logger.warning("No JSON found in LLM response")
        return None, None, "No JSON found in response"
    
    # Parse JSON
    try:
        raw_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {str(e)}")
        return None, None, f"Invalid JSON: {str(e)}"
    
    # Validate with Pydantic
    try:
        validated = model_class.model_validate(raw_dict)
        return validated, raw_dict, None
    except ValidationError as e:
        error_msg = str(e)
        logger.warning(f"Validation failed for {model_class.__name__}: {error_msg}")
        
        if strict:
            return None, raw_dict, error_msg
        
        # Return raw dict even if validation fails
        return None, raw_dict, error_msg


def create_retry_prompt(
    original_prompt: str,
    failed_response: str,
    error_message: str,
    model_class: Type[BaseModel]
) -> str:
    """
    Create a retry prompt with error feedback.
    
    Args:
        original_prompt: The original prompt that was sent
        failed_response: The response that failed validation
        error_message: The validation error message
        model_class: The expected Pydantic model
        
    Returns:
        New prompt with error feedback
    """
    schema = model_class.model_json_schema()
    
    return f"""Your previous response had validation errors. Please fix and respond with ONLY valid JSON.

ERROR: {error_message}

REQUIRED JSON SCHEMA:
{json.dumps(schema, indent=2)}

IMPORTANT:
- Return ONLY the JSON object, no markdown fences
- Ensure all required fields are present
- Use the exact field names and types from the schema

Please provide the corrected response:"""


class AgentResponseParser:
    """Parser for AI agent responses with retry capability."""
    
    def __init__(self, max_retries: int = 1):
        self.max_retries = max_retries
    
    async def parse_with_retry(
        self,
        llm,
        prompt: str,
        model_class: Type[T],
        initial_response: Optional[str] = None
    ) -> tuple[Optional[T], Dict[str, Any], str]:
        """
        Parse LLM response with retry on validation failure.
        
        Args:
            llm: LangChain LLM instance
            prompt: Original prompt
            model_class: Expected Pydantic model
            initial_response: Optional pre-fetched response
            
        Returns:
            Tuple of (validated_model, raw_dict, status)
        """
        from langchain_core.messages import HumanMessage
        
        response_text = initial_response
        
        for attempt in range(self.max_retries + 1):
            # Get response if not provided
            if response_text is None:
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                response_text = response.content
            
            # Try to parse
            validated, raw_dict, error = parse_llm_response(
                response_text, model_class, strict=True
            )
            
            if validated:
                return validated, validated.model_dump(), "success"
            
            if raw_dict:
                # Got valid JSON but failed Pydantic validation
                # Return raw dict as fallback
                logger.info(f"Using raw JSON (Pydantic validation failed)")
                return None, raw_dict, "partial"
            
            # No valid JSON, retry if attempts remaining
            if attempt < self.max_retries:
                logger.retry(model_class.__name__, attempt + 1, self.max_retries + 1, 0)
                retry_prompt = create_retry_prompt(
                    prompt, response_text, error, model_class
                )
                response_text = None
                prompt = retry_prompt
        
        # All retries failed
        return None, {"raw_response": response_text}, "error"


# Global parser instance
response_parser = AgentResponseParser(max_retries=1)
