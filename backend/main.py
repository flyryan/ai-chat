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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Environment variables
ENDPOINT = os.getenv("ENDPOINT_URL")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
SUBSCRIPTION_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=SUBSCRIPTION_KEY,
    api_version="2024-05-01-preview",
)

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: int = 800
    temperature: float = 0.7
    top_p: float = 0.95
    frequency_penalty: float = 0
    presence_penalty: float = 0

@app.get("/")
async def root():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        logger.info("Received chat request")
        # Convert messages to format expected by Azure OpenAI
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        completion = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stream=False,
            extra_body={
                "data_sources": [{
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": SEARCH_ENDPOINT,
                        "index_name": "ludus-trend-docs",
                        "semantic_configuration": "azureml-default",
                        "authentication": {
                            "type": "api_key",
                            "key": SEARCH_KEY
                        },
                        "embedding_dependency": {
                            "type": "endpoint",
                            "endpoint": f"{ENDPOINT}/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-07-01-preview",
                            "authentication": {
                                "type": "api_key",
                                "key": SUBSCRIPTION_KEY
                            }
                        },
                        "query_type": "vector_simple_hybrid",
                        "in_scope": True,
                        "strictness": 3,
                        "top_n_documents": 5
                    }
                }]
            }
        )
        
        return {
            "response": completion.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        while True:
            try:
                # Receive and parse the message
                data = await websocket.receive_text()
                request_data = json.loads(data)
                logger.info("Received WebSocket message")
                
                # Process the request similar to the HTTP endpoint
                messages = request_data.get("messages", [])
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                
                # Create completion with streaming
                completion = client.chat.completions.create(
                    model=DEPLOYMENT,
                    messages=messages,
                    stream=True,
                    max_tokens=request_data.get("max_tokens", 800),
                    temperature=request_data.get("temperature", 0.7),
                    extra_body={
                        "data_sources": [{
                            "type": "azure_search",
                            "parameters": {
                                "endpoint": SEARCH_ENDPOINT,
                                "index_name": "ludus-trend-docs",
                                "semantic_configuration": "azureml-default",
                                "authentication": {
                                    "type": "api_key",
                                    "key": SEARCH_KEY
                                },
                                "embedding_dependency": {
                                    "type": "endpoint",
                                    "endpoint": f"{ENDPOINT}/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-07-01-preview",
                                    "authentication": {
                                        "type": "api_key",
                                        "key": SUBSCRIPTION_KEY
                                    }
                                },
                                "query_type": "vector_simple_hybrid",
                                "in_scope": True,
                                "strictness": 3,
                                "top_n_documents": 5
                            }
                        }]
                    }
                )
                
                # Stream the response
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        await websocket.send_text(chunk.choices[0].delta.content)
                        
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                await websocket.send_text(f"Error: Invalid JSON format - {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_text(f"Error: {str(e)}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        if websocket.client_state.value:
            await websocket.close()

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Verify environment variables
    required_vars = ["ENDPOINT_URL", "DEPLOYMENT_NAME", "SEARCH_ENDPOINT", "SEARCH_KEY", "AZURE_OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.info("All required environment variables are set")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
