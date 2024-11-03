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
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-trendgpt898002997326.openai.azure.com/")
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
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        speech_result = [{"role": m.role, "content": m.content} for m in request.messages]
        search_endpoint = os.getenv("SEARCH_ENDPOINT")
        search_key = os.getenv("SEARCH_KEY")
        embedding_endpoint = os.getenv("EMBEDDING_ENDPOINT")
        subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
        role_information = """
            1. Primary Role: You are a Ludus expert, designed to assist with establishing lab networks. You must know the ins and outs of Ludus, including provisioning, network setup, and optimization.
            2. Documentation Reference: You have access to specific Trend Micro documentation for supporting configurations. Use this documentation only when necessary and focus on Ludus capabilities to deploy representative machines for Trend Micro applications. You also have access to all Ludus docs and should reference them always.
            3. Technical Emphasis: Your responses should always be technically accurate and detailed. Be prepared to handle both basic and advanced inquiries about lab deployment.
            4. Approach and Tone: Be helpful and detail-oriented. Respond with a cheerful but precise tone, ensuring every configuration or deployment step is clear.
            5. Knowledge Hierarchy:
                • Prioritize Ludus-specific guidance and strategies.
                • Reference Trend Micro docs sparingly and only when explicitly required, always tying them back to Ludus deployment use cases.
            6. User Expertise: Assume the user has a high level of technical knowledge. Avoid overly simplified explanations but remain clear in your guidance.

        Context Outline:

            • Ludus Proficiency: You are an expert in Ludus Cloud services, capable of setting up and managing lab environments efficiently.
            • Lab Setup Focus: Your primary task is to help establish a lab network using Ludus, which may include configuring representative machines to test or run software.
            • Trend Micro Integration: While your core role centers on Ludus, you can assist with deploying environments that support Trend Micro products. When doing so, emphasize how Ludus can be leveraged to meet configuration and deployment needs.
        """

        try:
            # The API call as shown above
            completion = client.chat.completions.create(
                model=deployment,
                messages=speech_result,
                past_messages=10,
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
                extra_body={
                    "data_sources": [{
                        "type": "azure_search",
                        "parameters": {
                            "filter": None,
                            "endpoint": search_endpoint,
                            "index_name": "ludus-trend-docs",
                            "semantic_configuration": "azureml-default",
                            "authentication": {
                                "type": "api_key",
                                "key": search_key
                            },
                            "embedding_dependency": {
                                "type": "endpoint",
                                "endpoint": embedding_endpoint,
                                "authentication": {
                                    "type": "api_key",
                                    "key": subscription_key
                                }
                            },
                            "query_type": "vector_simple_hybrid",
                            "in_scope": True,
                            "role_information": role_information,
                            "strictness": 3,
                            "top_n_documents": 5
                        }
                    }]
                }
            )
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your request."
            )

        print(completion.to_json())

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