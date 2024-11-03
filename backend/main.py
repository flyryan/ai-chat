import os
from fastapi import FastAPI, HTTPException, WebSocket, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import json
from openai import AzureOpenAI
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get frontend URL from environment variable or use default
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://salmon-grass-06d76a510.5.azurestaticapps.net")
ADDITIONAL_ORIGINS = os.getenv("ADDITIONAL_ORIGINS", "").split(",")

# Combine all allowed origins
ALLOWED_ORIGINS = [FRONTEND_URL] + [origin for origin in ADDITIONAL_ORIGINS if origin]
if "*" in ADDITIONAL_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

logger.info(f"Configured ALLOWED_ORIGINS: {ALLOWED_ORIGINS}")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 800
    temperature: Optional[float] = 0.7

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "allowed_origins": ALLOWED_ORIGINS,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("WebSocket connection established")
        
        while True:
            try:
                data = await websocket.receive_text()
                # Process the message and send response
                # Add your message handling logic here
                await websocket.send_text("Message received")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(f"Error processing message: {str(e)}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1001)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Your existing chat logic here
        return {
            "response": "Test response",
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
    uvicorn.run(app, host="0.0.0.0", port=8000)