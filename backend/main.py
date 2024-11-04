import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting application initialization...")

from fastapi import FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re
from openai import AzureOpenAI
from config import settings

# Create FastAPI app
app = FastAPI(title=settings.app_name)

def get_allowed_origins():
    """Get allowed origins with proper handling of wildcard domains"""
    origins = []
    for origin in settings.cors_origins:
        if '*' in origin:
            # Convert wildcard pattern to regex pattern
            pattern = re.escape(origin).replace('\\*', '.*')
            origins.append(re.compile(pattern))
        else:
            origins.append(origin)
    return origins

def is_origin_allowed(origin: str, allowed_origins) -> bool:
    """Check if origin is allowed, handling both exact matches and patterns"""
    if not origin:
        return False
    
    for allowed_origin in allowed_origins:
        if isinstance(allowed_origin, re.Pattern):
            if allowed_origin.match(origin):
                return True
        elif origin == allowed_origin:
            return True
    return False

allowed_origins = get_allowed_origins()
logger.info(f"Configured CORS origins: {settings.cors_origins}")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll handle validation ourselves
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def cors_middleware(request, call_next):
    """Custom CORS middleware to handle wildcard subdomains"""
    origin = request.headers.get("origin")
    logger.debug(f"Received request from origin: {origin}")

    response = await call_next(request)
    
    if origin:
        if is_origin_allowed(origin, allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "*"
            logger.debug(f"CORS headers set for origin: {origin}")
        else:
            logger.warning(f"Origin not allowed: {origin}")
    
    return response

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = 0.7

# Initialize OpenAI client with configuration
client = AzureOpenAI(
    api_key=settings.openai_api_key,
    api_version=settings.openai_api_version,
    azure_endpoint=str(settings.openai_api_base)
)

def prepare_vector_search_config() -> Optional[Dict[str, Any]]:
    """Prepare vector search configuration if enabled"""
    if not settings.vector_search_enabled:
        return None
        
    return {
        "type": "azure_cognitive_search",
        "parameters": {
            "endpoint": str(settings.vector_search_endpoint),
            "key": settings.vector_search_key,
            "indexName": settings.vector_search_index,
            "fieldsMapping": {
                "contentFields": ["content"],
                "titleField": "title",
                "urlField": "url",
                "filepathField": "filepath"
            },
            "inScope": True,
            "roleInformation": settings.system_prompt,
            "strictness": 3,
            "topNDocuments": 5
        }
    }

async def generate_chat_completion(messages: List[Dict[str, str]], max_tokens: int, temperature: float, stream: bool = False):
    """Generate chat completion with proper error handling"""
    try:
        completion_kwargs = {
            "model": settings.openai_deployment_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        
        # Add data sources if vector search is enabled
        vector_search_config = prepare_vector_search_config()
        if vector_search_config:
            completion_kwargs["extra_body"] = {
                "dataSources": [vector_search_config]
            }
            logger.info("Vector search enabled for completion")
        
        logger.debug(f"Calling OpenAI with parameters: {completion_kwargs}")
        return await client.chat.completions.create(**completion_kwargs)
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint for debugging"""
    return {
        "message": "API is running",
        "version": "1.0",
        "endpoints": [
            "/health",
            "/chat",
            "/ws"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint that returns configuration status"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "vector_search_enabled": settings.vector_search_enabled,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """HTTP endpoint for chat functionality"""
    logger.info("Received chat request")
    logger.debug(f"Request body: {request}")
    
    try:
        messages = [
            {"role": "system", "content": settings.system_prompt}
        ] + [
            {"role": m.role, "content": m.content} 
            for m in request.messages
        ]
        
        completion = await generate_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=False
        )

        response_data = {
            "response": completion.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        }
        logger.info("Successfully processed chat request")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat functionality"""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        while True:
            try:
                # Log the start of message processing
                data = await websocket.receive_text()
                logger.info("Received WebSocket message")
                logger.debug(f"Raw message content: {data}")
                
                try:
                    request_data = json.loads(data)
                    logger.debug(f"Parsed request data: {request_data}")
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON format: {str(e)}"
                    logger.error(error_msg)
                    await websocket.send_text(error_msg)
                    continue

                try:
                    chat_request = ChatRequest(**request_data)
                    logger.debug(f"Validated chat request: {chat_request}")
                except Exception as e:
                    error_msg = f"Invalid request format: {str(e)}"
                    logger.error(error_msg)
                    await websocket.send_text(error_msg)
                    continue
                
                messages = [
                    {"role": "system", "content": settings.system_prompt}
                ] + [
                    {"role": m.role, "content": m.content} 
                    for m in chat_request.messages
                ]
                
                logger.debug(f"Prepared messages: {messages}")
                logger.info("Preparing OpenAI API call")
                
                try:
                    completion_kwargs = {
                        "model": settings.openai_deployment_name,
                        "messages": messages,
                        "max_tokens": chat_request.max_tokens,
                        "temperature": chat_request.temperature,
                        "stream": True
                    }
                    
                    # Add vector search if enabled
                    if settings.vector_search_enabled:
                        logger.info("Vector search is enabled, adding configuration")
                        vector_search_config = {
                            "type": "azure_cognitive_search",
                            "parameters": {
                                "endpoint": str(settings.vector_search_endpoint),
                                "key": settings.vector_search_key,
                                "indexName": settings.vector_search_index,
                                "roleInformation": settings.system_prompt,
                                "strictness": 3,
                                "topNDocuments": 5
                            }
                        }
                        completion_kwargs["extra_body"] = {
                            "dataSources": [vector_search_config]
                        }
                        logger.debug("Added vector search configuration")
                    
                    logger.debug(f"Final completion kwargs: {completion_kwargs}")
                    completion = await client.chat.completions.create(**completion_kwargs)
                    
                    # Process streaming response
                    async for chunk in completion:
                        if chunk.choices[0].delta.content:
                            await websocket.send_text(chunk.choices[0].delta.content)
                    
                except Exception as e:
                    error_msg = f"OpenAI API error: {str(e)}"
                    logger.error(error_msg)
                    logger.exception(e)
                    await websocket.send_text(f"Error: {str(e)}")
                    
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg)
                logger.exception(e)
                await websocket.send_text(f"Error: {str(e)}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        logger.exception(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )