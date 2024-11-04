from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from functools import lru_cache

class OpenAISettings(BaseModel):
    """Settings specific to Azure OpenAI integration"""
    api_key: str = Field(..., description="Azure OpenAI API key")
    api_base: HttpUrl = Field(..., description="Azure OpenAI base URL")
    api_version: str = Field(default="2023-05-15", description="Azure OpenAI API version")
    deployment_name: str = Field(..., description="Model deployment name")
    temperature: float = Field(default=0.7, description="Model temperature (0-1)")
    max_tokens: int = Field(default=4000, description="Maximum tokens per response")

class VectorSearchSettings(BaseModel):
    """Settings specific to Azure Vector Search integration"""
    enabled: bool = Field(default=False, description="Whether vector search is enabled")
    endpoint: Optional[HttpUrl] = Field(default=None, description="Vector search endpoint URL")
    key: Optional[str] = Field(default=None, description="Vector search API key")
    index_name: Optional[str] = Field(default=None, description="Vector search index name")
    semantic_config: str = Field(default="default", description="Semantic configuration name")
    query_type: str = Field(default="vector_simple_hybrid", description="Query type for vector search")
    strictness: int = Field(default=3, description="Search strictness level (1-5)")
    top_n_documents: int = Field(default=5, description="Number of documents to retrieve")

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
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=4000, alias="OPENAI_MAX_TOKENS")
    
    # Vector Search configuration
    vector_search_enabled: bool = Field(default=False, alias="VECTOR_SEARCH_ENABLED")
    vector_search_endpoint: Optional[HttpUrl] = Field(default=None, alias="VECTOR_SEARCH_ENDPOINT")
    vector_search_key: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_KEY")
    vector_search_index: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_INDEX")
    vector_search_semantic_config: str = Field(default="default", alias="VECTOR_SEARCH_SEMANTIC_CONFIG")
    vector_search_query_type: str = Field(default="vector_simple_hybrid", alias="VECTOR_SEARCH_QUERY_TYPE")
    vector_search_strictness: int = Field(default=3, alias="VECTOR_SEARCH_STRICTNESS")
    vector_search_top_n: int = Field(default=5, alias="VECTOR_SEARCH_TOP_N")

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
    def openai_settings(self) -> OpenAISettings:
        """Get OpenAI settings"""
        return OpenAISettings(
            api_key=self.openai_api_key,
            api_base=self.openai_api_base,
            api_version=self.openai_api_version,
            deployment_name=self.openai_deployment_name,
            temperature=self.openai_temperature,
            max_tokens=self.openai_max_tokens
        )

    @property
    def vector_search_settings(self) -> VectorSearchSettings:
        """Get Vector Search settings"""
        return VectorSearchSettings(
            enabled=self.vector_search_enabled,
            endpoint=self.vector_search_endpoint,
            key=self.vector_search_key,
            index_name=self.vector_search_index,
            semantic_config=self.vector_search_semantic_config,
            query_type=self.vector_search_query_type,
            strictness=self.vector_search_strictness,
            top_n_documents=self.vector_search_top_n
        )

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
    print(f"OpenAI Settings: {s.openai_settings.model_dump()}")
    if s.vector_search_enabled:
        print(f"Vector Search Settings: {s.vector_search_settings.model_dump()}")