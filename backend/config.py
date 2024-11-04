from typing import Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlparse as URL
import os
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

def parse_cors_origins(v: Union[str, List[str]]) -> List[str]:
    """Parse CORS origins from string or list"""
    if isinstance(v, str):
        # Split by comma and clean up each URL
        origins = [origin.strip() for origin in v.split(",")]
        # Filter out empty strings
        origins = [origin for origin in origins if origin]
        # Add secure variants if needed
        expanded_origins = []
        for origin in origins:
            expanded_origins.append(origin)
            # Add https variant if http is specified
            if origin.startswith("http://"):
                expanded_origins.append(origin.replace("http://", "https://"))
            # Add azurestaticapps.net variants
            if "azurestaticapps.net" in origin:
                base_domain = origin.split("://")[1].split(".azurestaticapps.net")[0]
                expanded_origins.append(f"https://{base_domain}.azurestaticapps.net")
                expanded_origins.append(f"http://{base_domain}.azurestaticapps.net")
        return list(set(expanded_origins))
    elif isinstance(v, list):
        return v
    raise ValueError("CORS_ORIGINS must be a string or list")

class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Basic configuration
    app_name: str = Field(default="AI Chat Assistant")
    environment: str = Field(default="production")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # CORS configuration
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "https://*.azurestaticapps.net"],
        description="Allowed CORS origins as comma-separated string or list"
    )

    # OpenAI configuration
    openai_api_key: str = Field(...)
    openai_api_base: HttpUrl = Field(...)
    openai_api_version: str = Field(default="2024-05-01-preview")
    openai_deployment_name: str = Field(...)
    openai_temperature: float = Field(default=0.7)
    openai_max_tokens: int = Field(default=4000)
    openai_top_p: float = Field(default=0.95)
    openai_frequency_penalty: float = Field(default=0)
    openai_presence_penalty: float = Field(default=0)
    
    # Vector Search configuration
    vector_search_enabled: bool = Field(default=False)
    vector_search_endpoint: Optional[HttpUrl] = None
    vector_search_key: Optional[str] = None
    vector_search_index: Optional[str] = None
    vector_search_semantic_config: str = Field(default="azureml-default")
    vector_search_embedding_deployment: str = Field(default="text-embedding-ada-002")

    # System configuration
    system_prompt: str = Field(
        default="You are an AI assistant. You aim to be helpful, honest, and direct in your interactions."
    )

    @field_validator('vector_search_enabled', mode='before')
    def validate_vector_search(cls, v: Any, info: ValidationInfo) -> bool:
        """Validate vector search configuration if enabled"""
        # Convert string 'true'/'false' to boolean if necessary
        if isinstance(v, str):
            v = v.lower() == 'true'
        
        if not v:
            return False

        data = info.data
        required_fields = ['vector_search_endpoint', 'vector_search_key', 'vector_search_index']
        
        # Check if required fields are present and not empty
        missing = []
        for field in required_fields:
            field_value = data.get(field)
            if not field_value or str(field_value).strip() == '':
                missing.append(field)
        
        if missing:
            # Instead of raising an error, log a warning and disable vector search
            logger.warning(
                f"Vector search is enabled but missing required fields: {', '.join(missing)}. "
                "Disabling vector search functionality."
            )
            return False
            
        # Validate endpoint URL if present
        if 'vector_search_endpoint' in data and data['vector_search_endpoint']:
            try:
                URL(str(data['vector_search_endpoint']))
            except Exception as e:
                logger.warning(f"Invalid vector search endpoint URL: {e}. Disabling vector search.")
                return False

        return True

    @field_validator('cors_origins')
    def validate_cors_origins(cls, v):
        return parse_cors_origins(v)

    def model_post_init(self, _context):
        """Log loaded configuration for debugging"""
        logger.info("Loaded configuration:")
        logger.info(f"App Name: {self.app_name}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"CORS Origins: {self.cors_origins}")
        
        if self.vector_search_enabled:
            logger.info("Vector search is enabled")
            logger.info(f"Vector Search Endpoint: {self.vector_search_endpoint}")
            logger.info(f"Vector Search Index: {self.vector_search_index}")
        else:
            logger.info("Vector search is disabled")

# Create settings instance
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    logger.info("Loading settings...")
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        raise

# Initialize settings once at module level
settings = get_settings()