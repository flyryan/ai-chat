from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from functools import lru_cache

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
    embedding_deployment: str = Field(default="text-embedding-ada-002", description="Embedding model deployment name")

class OpenAISettings(BaseModel):
    """Settings specific to Azure OpenAI integration"""
    api_key: str = Field(..., description="Azure OpenAI API key")
    api_base: HttpUrl = Field(..., description="Azure OpenAI base URL")
    api_version: str = Field(default="2023-05-15", description="Azure OpenAI API version")
    deployment_name: str = Field(..., description="Model deployment name")
    temperature: float = Field(default=0.7, description="Model temperature (0-1)")
    max_tokens: int = Field(default=4000, description="Maximum tokens per response")

class ServerSettings(BaseModel):
    """Web server specific settings"""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    websocket_ping_interval: int = Field(
        default=30,
        description="WebSocket ping interval in seconds"
    )
    connection_timeout: int = Field(
        default=60,
        description="Connection timeout in seconds"
    )

class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    # Basic configuration
    app_name: str = Field(
        default="AI Chat Assistant",
        description="Application name"
    )
    environment: str = Field(
        default="production",
        description="Deployment environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )

    # CORS configuration with improved parsing
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
        description="Allowed CORS origins as comma-separated string or list"
    )

    # Component configurations
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_api_base: HttpUrl = Field(..., alias="OPENAI_API_BASE")
    openai_api_version: str = Field(default="2023-05-15", alias="OPENAI_API_VERSION")
    openai_deployment_name: str = Field(..., alias="OPENAI_DEPLOYMENT_NAME")
    
    vector_search_enabled: bool = Field(default=False, alias="VECTOR_SEARCH_ENABLED")
    vector_search_endpoint: Optional[HttpUrl] = Field(default=None, alias="VECTOR_SEARCH_ENDPOINT")
    vector_search_key: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_KEY")
    vector_search_index: Optional[str] = Field(default=None, alias="VECTOR_SEARCH_INDEX")

    # System configuration
    system_prompt: str = Field(
        default="You are an AI assistant. You aim to be helpful, honest, and direct in your interactions.",
        description="Default system prompt for the AI"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
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
                # Add www variant if not present
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
            deployment_name=self.openai_deployment_name
        )

    @property
    def vector_search_settings(self) -> VectorSearchSettings:
        """Get Vector Search settings"""
        return VectorSearchSettings(
            enabled=self.vector_search_enabled,
            endpoint=self.vector_search_endpoint,
            key=self.vector_search_key,
            index_name=self.vector_search_index
        )

    @property
    def server_settings(self) -> ServerSettings:
        """Get Server settings"""
        return ServerSettings(
            cors_origins=self.cors_origins
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