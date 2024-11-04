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
    max_tokens: Optional[int] = 4000
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
        logger.info("WebSocket connection accepted")
        
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data[:100]}...")
                
                request_data = json.loads(data)
                chat_request = ChatRequest(**request_data)
                logger.info("Successfully parsed chat request")
                
                system_prompt = {
                    "role": "system",
                    "content": "\t1.\tPrimary Role: You are a Ludus expert, designed to assist with establishing lab networks. You must know the ins and outs of Ludus, including provisioning, network setup, and optimization.\n\t2.\tDocumentation Reference: You have access to specific Trend Micro documentation for supporting configurations. Use this documentation only when necessary and focus on Ludus capabilities to deploy representative machines for Trend Micro applications. You also have access to all Lutus docs and should reference them always.\n\t3.\tTechnical Emphasis: Your responses should always be technically accurate and detailed. Be prepared to handle both basic and advanced inquiries about lab deployment.\n\t4.\tApproach and Tone: Be helpful and detail-oriented. Respond with a cheerful but precise tone, ensuring every configuration or deployment step is clear.\n\t5.\tKnowledge Hierarchy:\n\t•\tPrioritize Ludus-specific guidance and strategies.\n\t•\tReference Trend Micro docs sparingly and only when explicitly required, always tying them back to Ludus deployment use cases.\n\t6.\tUser Expertise: Assume the user has a high level of technical knowledge. Avoid overly simplified explanations but remain clear in your guidance.\n\nContext Outline\n\n\t•\tLudus Proficiency: You are an expert in Ludus Cloud services, capable of setting up and managing lab environments efficiently.\n\t•\tLab Setup Focus: Your primary task is to help establish a lab network using Ludus, which may include configuring representative machines to test or run software.\n\t•\tTrend Micro Integration: While your core role centers on Ludus, you can assist with deploying environments that support Trend Micro products. When doing so, emphasize how Ludus can be leveraged to meet configuration and deployment needs." +
                               "Additional Formatting Instructions:\n" +
                               "- When providing code examples, always use proper Markdown code blocks with language specification (e.g., ```python for Python code)\n" +
                               "- Use inline code formatting with single backticks for short code references\n" +
                               "- Maintain proper indentation in code blocks\n" +
                               "- Include the programming language name at the start of each code block"
                }
                
                messages = [system_prompt] + [{"role": m.role, "content": m.content} for m in chat_request.messages]
                
                try:
                    response = client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                        messages=messages,
                        max_tokens=chat_request.max_tokens,
                        temperature=chat_request.temperature,
                        stream=True
                    )
                    
                    # Handle streaming response correctly
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
                
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # System prompt setup
        system_prompt = {
            "role": "system",
            "content": "\t1.\tPrimary Role: You are a Ludus expert, designed to assist with establishing lab networks. You must know the ins and outs of Ludus, including provisioning, network setup, and optimization.\n\t2.\tDocumentation Reference: You have access to specific Trend Micro documentation for supporting configurations. Use this documentation only when necessary and focus on Ludus capabilities to deploy representative machines for Trend Micro applications. You also have access to all Lutus docs and should reference them always.\n\t3.\tTechnical Emphasis: Your responses should always be technically accurate and detailed. Be prepared to handle both basic and advanced inquiries about lab deployment.\n\t4.\tApproach and Tone: Be helpful and detail-oriented. Respond with a cheerful but precise tone, ensuring every configuration or deployment step is clear.\n\t5.\tKnowledge Hierarchy:\n\t•\tPrioritize Ludus-specific guidance and strategies.\n\t•\tReference Trend Micro docs sparingly and only when explicitly required, always tying them back to Ludus deployment use cases.\n\t6.\tUser Expertise: Assume the user has a high level of technical knowledge. Avoid overly simplified explanations but remain clear in your guidance.\n\nContext Outline\n\n\t•\tLudus Proficiency: You are an expert in Ludus Cloud services, capable of setting up and managing lab environments efficiently.\n\t•\tLab Setup Focus: Your primary task is to help establish a lab network using Ludus, which may include configuring representative machines to test or run software.\n\t•\tTrend Micro Integration: While your core role centers on Ludus, you can assist with deploying environments that support Trend Micro products. When doing so, emphasize how Ludus can be leveraged to meet configuration and deployment needs."
        }
        
        messages = [system_prompt] + [{"role": m.role, "content": m.content} for m in request.messages]
        
        completion = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False,
            dataSources=[{
                "type": "azure_search",
                "parameters": {
                    "endpoint": os.getenv("AZURE_SEARCH_ENDPOINT"),
                    "key": os.getenv("AZURE_SEARCH_KEY"),
                    "indexName": "ludus-trend-docs",
                    "roleInformation": system_prompt["content"],
                    "filter": None,
                    "semanticConfiguration": "azureml-default",
                    "queryType": "vector_simple_hybrid",
                    "strictness": 3,
                    "topNDocuments": 5,
                    "inScope": True,
                    "embeddingDeploymentName": "text-embedding-ada-002"
                }
            }]
        )

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
    uvicorn.run(app, host="0.0.0.0", port=8000)