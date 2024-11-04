import logging
import re
from fastapi import FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting application initialization...")

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

from pydantic import BaseModel
from typing import List, Optional
import json
from openai import AzureOpenAI
from datetime import datetime

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat functionality"""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data[:100]}...")
                
                request_data = json.loads(data)
                chat_request = ChatRequest(**request_data)
                
                messages = [
                    {"role": "system", "content": settings.system_prompt}
                ] + [
                    {"role": m.role, "content": m.content} 
                    for m in chat_request.messages
                ]
                
                try:
                    response = client.chat.completions.create(
                        model=settings.openai_deployment_name,
                        messages=messages,
                        max_tokens=chat_request.max_tokens,
                        temperature=chat_request.temperature,
                        stream=True
                    )
                    
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            await websocket.send_text(chunk.choices[0].delta.content)
                            
                except Exception as e:
                    logger.error(f"Error in OpenAI API call: {str(e)}")
                    await websocket.send_text(f"Error: {str(e)}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                await websocket.send_text("Invalid JSON format")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_text(f"Error: {str(e)}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """HTTP endpoint for chat functionality"""
    try:
        messages = [
            {"role": "system", "content": settings.system_prompt}
        ] + [
            {"role": m.role, "content": m.content} 
            for m in request.messages
        ]
        
        completion_kwargs = {
            "model": settings.openai_deployment_name,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,
        }
        
        # Add vector search if enabled
        if settings.vector_search_enabled:
            completion_kwargs["dataSources"] = [{
                "type": "azure_search",
                "parameters": {
                    "endpoint": str(settings.vector_search_endpoint),
                    "key": settings.vector_search_key,
                    "indexName": settings.vector_search_index,
                    "roleInformation": settings.system_prompt,
                    "filter": None,
                    "semanticConfiguration": settings.vector_search_semantic_config,
                    "queryType": settings.vector_search_query_type,
                    "strictness": settings.vector_search_strictness,
                    "topNDocuments": settings.vector_search_top_n,
                    "inScope": True,
                }
            }]

        completion = client.chat.completions.create(**completion_kwargs)

        return {
            "response": completion.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development
    )