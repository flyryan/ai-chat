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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get frontend URL from environment variable or use default
FRONTEND_URL = "https://salmon-grass-06d76a510.5.azurestaticapps.net"
FRONTEND_URLS = [
    FRONTEND_URL,
    "https://salmon-grass-06d76a5.restaticapps.net",
    "https://salmon-grass-06d76a510.5.azurestaticapps.net",
    # Add variations without https://
    "salmon-grass-06d76a510.5.azurestaticapps.net",
    "salmon-grass-06d76a5.restaticapps.net",
    # Add www variations
    "www.salmon-grass-06d76a510.5.azurestaticapps.net",
    "www.salmon-grass-06d76a5.restaticapps.net",
]

# Add both http and https variants
FRONTEND_URLS = [
    f"https://{url}" if not url.startswith('http') else url
    for url in FRONTEND_URLS
] + [
    f"http://{url}" if not url.startswith('http') else url.replace('https://', 'http://')
    for url in FRONTEND_URLS
]

# Add localhost for development
if os.getenv("ENVIRONMENT") == "development":
    FRONTEND_URLS.extend([
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000"
    ])

# Remove duplicates while preserving order
FRONTEND_URLS = list(dict.fromkeys(FRONTEND_URLS))

logger.info(f"Configured FRONTEND_URLS: {FRONTEND_URLS}")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
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
    max_tokens: Optional[int] = 800
    temperature: Optional[float] = 0.7

# Initialize Azure OpenAI client with proper configuration
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "allowed_origins": FRONTEND_URLS,
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
                request_data = json.loads(data)
                chat_request = ChatRequest(**request_data)
                
                response = client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    messages=[{"role": m.role, "content": m.content} for m in chat_request.messages],
                    max_tokens=chat_request.max_tokens,
                    temperature=chat_request.temperature,
                    stream=True  # Enable streaming
                )
                
                # Stream the response
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        await websocket.send_text(chunk.choices[0].delta.content)
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(f"Error: {str(e)}")
                
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