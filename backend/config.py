from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Main application settings with case-insensitive environment variables"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # Make environment variables case-insensitive
    )

    # Basic configuration
    app_name: str = Field(
        default="AI Chat Assistant",
        validation_alias="APP_NAME",
        alias="app_name"
    )
    environment: str = Field(
        default="production",
        validation_alias="ENVIRONMENT",
        alias="environment"
    )
    debug: bool = Field(
        default=False,
        validation_alias="DEBUG",
        alias="debug"
    )

    # CORS configuration
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000"],
        validation_alias="CORS_ORIGINS",
        alias="cors_origins"
    )

    # OpenAI configuration
    openai_api_key: str = Field(
        ...,
        validation_alias="OPENAI_API_KEY",
        alias="openai_api_key"
    )
    openai_api_base: HttpUrl = Field(
        ...,
        validation_alias="OPENAI_API_BASE",
        alias="openai_api_base"
    )
    openai_api_version: str = Field(
        default="2023-05-15",
        validation_alias="OPENAI_API_VERSION",
        alias="openai_api_version"
    )
    openai_deployment_name: str = Field(
        ...,
        validation_alias="OPENAI_DEPLOYMENT_NAME",
        alias="openai_deployment_name"
    )
    
    # Vector Search configuration
    vector_search_enabled: bool = Field(
        default=False,
        validation_alias="VECTOR_SEARCH_ENABLED",
        alias="vector_search_enabled"
    )
    vector_search_endpoint: Optional[HttpUrl] = Field(
        default=None,
        validation_alias="VECTOR_SEARCH_ENDPOINT",
        alias="vector_search_endpoint"
    )
    vector_search_key: Optional[str] = Field(
        default=None,
        validation_alias="VECTOR_SEARCH_KEY",
        alias="vector_search_key"
    )
    vector_search_index: Optional[str] = Field(
        default=None,
        validation_alias="VECTOR_SEARCH_INDEX",
        alias="vector_search_index"
    )

    # System configuration
    system_prompt: str = Field(
        default="You are an AI assistant. You aim to be helpful, honest, and direct in your interactions.",
        validation_alias="SYSTEM_PROMPT",
        alias="system_prompt"
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

    def model_post_init(self, _context):
        """Log loaded configuration for debugging"""
        logger.info(f"Loaded configuration:")
        logger.info(f"APP_NAME: {self.app_name}")
        logger.info(f"ENVIRONMENT: {self.environment}")
        logger.info(f"CORS_ORIGINS: {self.cors_origins}")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    logger.info("Loading settings...")
    try:
        settings = Settings()
        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        raise

# Create settings instance
settings = get_settings()