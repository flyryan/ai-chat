from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
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

    # CORS configuration
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "https://*.azurestaticapps.net"],
        description="Allowed CORS origins as comma-separated string or list"
    )

    @field_validator("cors_origins")
    def validate_cors_origins(cls, v):
        return parse_cors_origins(v)

    # Rest of your settings...

    def model_post_init(self, _context):
        """Log loaded configuration for debugging"""
        logger.info("Loaded configuration:")
        logger.info(f"App Name: {self.app_name}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"CORS Origins: {self.cors_origins}")