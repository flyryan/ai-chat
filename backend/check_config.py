#!/usr/bin/env python3
"""
Configuration validation script for AI Chat Assistant
Run this before deployment to validate all settings
"""

import sys
from pathlib import Path
from config import Settings, get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_configuration():
    """Validate all configuration settings"""
    try:
        settings = get_settings()
        
        # Basic validation
        logger.info(f"App Name: {settings.app_name}")
        logger.info(f"Environment: {settings.environment}")
        
        # Test CORS origins parsing
        logger.info(f"CORS Origins: {settings.cors_origins}")
        
        # Validate OpenAI settings
        openai_config = settings.openai_settings
        logger.info("OpenAI Configuration:")
        logger.info(f"  API Base: {openai_config.api_base}")
        logger.info(f"  API Version: {openai_config.api_version}")
        logger.info(f"  Deployment: {openai_config.deployment_name}")
        
        # Check vector search configuration if enabled
        if settings.vector_search_enabled:
            vector_config = settings.vector_search_settings
            logger.info("Vector Search Configuration:")
            logger.info(f"  Endpoint: {vector_config.endpoint}")
            logger.info(f"  Index: {vector_config.index_name}")
            
        logger.info("Configuration validation successful!")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Validating configuration...")
    if not validate_configuration():
        sys.exit(1)
    sys.exit(0)
