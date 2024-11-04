from typing import Optional
from pydantic import BaseSettings, HttpUrl, validator
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Basic configuration
    APP_NAME: str = "AI Chat Assistant"
    ENVIRONMENT: str = "production"
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str
    OPENAI_API_BASE: HttpUrl
    OPENAI_API_VERSION: str = "2023-05-15"
    OPENAI_DEPLOYMENT_NAME: str
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 4000
    
    # Optional Vector Search Configuration
    VECTOR_SEARCH_ENABLED: bool = False
    VECTOR_SEARCH_ENDPOINT: Optional[HttpUrl] = None
    VECTOR_SEARCH_KEY: Optional[str] = None
    VECTOR_SEARCH_INDEX: Optional[str] = None
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # System Prompt Configuration
    SYSTEM_PROMPT: str = """You are an AI assistant. You aim to be helpful, honest, and direct in your interactions."""
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Use lru_cache to avoid reading the environment multiple times.
    """
    return Settings()

# Create settings instance
settings = get_settings()
