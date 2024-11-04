from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # Make environment variables case-insensitive
    )

    # Basic configuration
    app_name: str = Field(
        default="AI Chat Assistant",
        alias="APP_NAME",
        description="Application name"
    )
    environment: str = Field(
        default="production",
        alias="ENVIRONMENT",
        description="Deployment environment"
    )
    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Debug mode flag"
    )

    # CORS configuration
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
        description="Allowed CORS origins as comma-separated string or list"
    )

    # OpenAI configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_api_base: HttpUrl = Field(..., alias="OPENAI_API_BASE")
    openai_api_version: str = Field(default="2023-05-15", alias="OPENAI_API_VERSION")
    openai_deployment_name: str = Field(..., alias="OPENAI_DEPLOYMENT_NAME")
    
    # Vector Search configuration
    vector_search_enabled: bool = Field(default=False, alias="VECTOR_SEARCH_ENABLED")
    vector_search_endpoint: Optional[HttpUrl] = Field(default=None, alias="VECTOR_SEARCH_ENDPOINT")
    vector_search_key: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_KEY")
    vector_search_index: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_INDEX")

    # System configuration
    system_prompt: str = Field(
        default="You are an AI assistant. You aim to be helpful, honest, and direct in your interactions.",
        alias="SYSTEM_PROMPT",
        description="Default system prompt for the AI"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",")]
            origins = [origin for origin in origins if origin]
            expanded_origins = []
            for origin in origins:
                expanded_origins.append(origin)
                if origin.startswith("http://"):
                    expanded_origins.append(origin.replace("http://", "https://"))
                if not origin.startswith("www."):
                    www_variant = origin.replace("://", "://www.")
                    expanded_origins.append(www_variant)
            return list(set(expanded_origins))
        elif isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS must be a string or list")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Create settings instance
settings = get_settings()

if __name__ == "__main__":
    # Print current settings for debugging
    s = get_settings()
    print(f"Application Name: {s.app_name}")
    print(f"Environment: {s.environment}")
    print(f"CORS Origins: {s.cors_origins}")