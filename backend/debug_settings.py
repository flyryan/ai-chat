#!/usr/bin/env python3
"""
Debug script to check environment variables and settings
"""
import os
from config import settings

def debug_settings():
    print("\n=== Environment Variables ===")
    env_vars = [
        'APP_NAME', 'ENVIRONMENT', 'DEBUG',
        'CORS_ORIGINS',
        'OPENAI_API_KEY', 'OPENAI_API_BASE', 'OPENAI_API_VERSION', 'OPENAI_DEPLOYMENT_NAME',
        'VECTOR_SEARCH_ENABLED', 'VECTOR_SEARCH_ENDPOINT', 'VECTOR_SEARCH_INDEX',
        'SYSTEM_PROMPT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if var.endswith('KEY'):
            print(f"{var}: {'***' if value else 'Not set'}")
        else:
            print(f"{var}: {value or 'Not set'}")

    print("\n=== Settings Values ===")
    print(f"app_name: {settings.app_name}")
    print(f"environment: {settings.environment}")
    print(f"cors_origins: {settings.cors_origins}")
    print(f"openai_api_base: {settings.openai_api_base}")
    print(f"openai_deployment_name: {settings.openai_deployment_name}")
    print(f"vector_search_enabled: {settings.vector_search_enabled}")

if __name__ == "__main__":
    debug_settings()
