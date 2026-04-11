"""
Core Configuration Module - Centralized settings from environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Google Gemini API
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Groq API (for DeepSeek and other LLMs)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # External Data APIs
    MORALIS_API_KEY: Optional[str] = os.getenv("MORALIS_API_KEY")
    APIFY_API_TOKEN: Optional[str] = os.getenv("APIFY_API_TOKEN")
    TWITTER_API_KEY: Optional[str] = os.getenv("TWITTER_API_KEY")
    GOPLUS_API_KEY: Optional[str] = os.getenv("GOPLUS_API_KEY")
    HELIUS_API_KEY: Optional[str] = os.getenv("HELIUS_API_KEY")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS Configuration
    CORS_ORIGINS: list = [
        origin for origin in [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            os.getenv("FRONTEND_URL", ""),
        ] if origin
    ]

    @classmethod
    def validate(cls) -> list[str]:
        """Validate that all required settings are configured.

        Returns:
            List of missing configuration keys.
        """
        missing = []
        required_keys = [
            ("GOOGLE_API_KEY", cls.GOOGLE_API_KEY),
            ("GROQ_API_KEY", cls.GROQ_API_KEY),
        ]

        for name, value in required_keys:
            if not value:
                missing.append(name)

        return missing


# Global settings instance
settings = Settings()
