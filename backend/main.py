import os
from fastapi import FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from openai import AzureOpenAI
from datetime import datetime
import logging
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = settings.OPENAI_MAX_TOKENS
    temperature: Optional[float] = settings.OPENAI_TEMPERATURE

# Initialize OpenAI client with configuration
client = AzureOpenAI(
    api_key=settings.OPENAI_API_KEY,
    api_version=settings.OPENAI_API_VERSION,
    azure_endpoint=settings.OPENAI_API_BASE
)

@app.get("/health")
async def health():
    """Health check endpoint that returns configuration status"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "vector_search_enabled": settings.VECTOR_SEARCH_ENABLED,
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
                    {"role": "system", "content": settings.SYSTEM_PROMPT}
                ] + [
                    {"role": m.role, "content": m.content} 
                    for m in chat_request.messages
                ]
                
                try:
                    response = client.chat.completions.create(
                        model=settings.OPENAI_DEPLOYMENT_NAME,
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
            {"role": "system", "content": settings.SYSTEM_PROMPT}
        ] + [
            {"role": m.role, "content": m.content} 
            for m in request.messages
        ]
        
        completion_kwargs = {
            "model": settings.OPENAI_DEPLOYMENT_NAME,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,
        }
        
        # Add vector search if enabled
        if settings.VECTOR_SEARCH_ENABLED:
            completion_kwargs["dataSources"] = [{
                "type": "azure_search",
                "parameters": {
                    "endpoint": settings.VECTOR_SEARCH_ENDPOINT,
                    "key": settings.VECTOR_SEARCH_KEY,
                    "indexName": settings.VECTOR_SEARCH_INDEX,
                    "roleInformation": settings.SYSTEM_PROMPT,
                    "filter": None,
                    "semanticConfiguration": "default",
                    "queryType": "vector_simple_hybrid",
                    "strictness": 3,
                    "topNDocuments": 5,
                    "inScope": True,
                    "embeddingDeploymentName": "text-embedding-ada-002"
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
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )