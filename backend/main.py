import logging
import contextlib
import weakref
from typing import Set, Optional, Dict
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, status
import aiohttp
import time

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
    azure_endpoint=settings.openai_api_base,
    api_key=settings.openai_api_key,
    api_version="2024-05-01-preview"
)

def prepare_vector_search_config() -> Dict[str, Any]:
    """Prepare vector search configuration based on working reference"""
    return {
        "data_sources": [{
            "type": "azure_search",
            "parameters": {
                "filter": None,
                "endpoint": str(settings.vector_search_endpoint),
                "index_name": settings.vector_search_index,
                "semantic_configuration": "azureml-default",
                "authentication": {
                    "type": "api_key",
                    "key": settings.vector_search_key
                },
                "embedding_dependency": {
                    "type": "endpoint",
                    "endpoint": f"{settings.openai_api_base}/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-07-01-preview",
                    "authentication": {
                        "type": "api_key",
                        "key": settings.openai_api_key
                    }
                },
                "query_type": "vector_simple_hybrid",
                "in_scope": True,
                "role_information": settings.system_prompt,
                "strictness": 3,
                "top_n_documents": 5
            }
        }]
    }

class StreamMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.chunk_count = 0
        self.total_tokens = 0
        self.errors = 0
        
    def record_chunk(self, chunk):
        self.chunk_count += 1
        if hasattr(chunk, 'usage') and hasattr(chunk.usage, 'total_tokens'):
            self.total_tokens += chunk.usage.total_tokens
            
    def record_error(self):
        self.errors += 1
        
    def get_metrics(self):
        duration = time.time() - self.start_time
        return {
            "duration_seconds": round(duration, 2),
            "chunk_count": self.chunk_count,
            "total_tokens": self.total_tokens,
            "errors": self.errors,
            "chunks_per_second": round(self.chunk_count / duration if duration > 0 else 0, 2)
        }

async def monitor_stream(stream):
    metrics = StreamMetrics()
    try:
        async for chunk in stream:
            try:
                metrics.record_chunk(chunk)
                yield chunk
            except Exception as e:
                metrics.record_error()
                logger.error(f"Error processing chunk: {e}")
    finally:
        logger.info(f"Stream metrics: {metrics.get_metrics()}")

async def generate_chat_completion(messages: List[Dict[str, str]], max_tokens: int, temperature: float, stream: bool = False):
    """Generate chat completion with robust stream handling and proper vector search"""
    try:
        completion_kwargs = {
            "model": settings.openai_deployment_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": stream,
        }
        
        if settings.vector_search_enabled:
            # Validate required settings
            if not all([
                settings.vector_search_endpoint,
                settings.vector_search_key,
                settings.vector_search_index
            ]):
                logger.error("Vector search is enabled but required settings are missing")
                raise ValueError("Incomplete vector search configuration")

            # Configure vector search with explicit data source
            completion_kwargs["dataSources"] = [{
                "type": "azure_search",
                "parameters": {
                    "endpoint": str(settings.vector_search_endpoint),
                    "key": settings.vector_search_key,
                    "indexName": settings.vector_search_index,
                    "semanticConfiguration": settings.vector_search_semantic_config,
                    "queryType": "vector_simple_hybrid",
                    "inScope": True,
                    "roleInformation": settings.system_prompt,
                    "strictness": 3,
                    "topNDocuments": 5,
                    "filter": "",  # Add any filtering conditions if needed
                    "embeddingDeploymentName": settings.vector_search_embedding_deployment
                }
            }]
            
            logger.info(f"Vector search enabled with index: {settings.vector_search_index}")
            logger.debug(f"Vector search configuration: {completion_kwargs['dataSources']}")
        
        logger.debug(f"Calling OpenAI with parameters: {completion_kwargs}")
        
        if stream:
            async def stream_generator():
                stream_response = client.chat.completions.create(**completion_kwargs)
                for chunk in stream_response:
                    yield chunk
            return stream_generator()
        else:
            completion = client.chat.completions.create(**completion_kwargs)
            return completion
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )

async def validate_openai_config():
    """Validate OpenAI configuration by making a test request"""
    try:
        logger.info(f"Validating OpenAI configuration...")
        logger.info(f"API Base: {settings.openai_api_base}")
        logger.info(f"API Version: {settings.openai_api_version}")
        logger.info(f"Deployment Name: {settings.openai_deployment_name}")
        
        test_completion = client.chat.completions.create(
            model=settings.openai_deployment_name,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10,
            temperature=0,
            stream=False
        )
        logger.info("OpenAI configuration validated successfully")
        return True
    except Exception as e:
        logger.error(f"OpenAI configuration validation failed: {str(e)}")
        logger.exception(e)
        return False

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    if not await validate_openai_config():
        logger.error("Failed to validate OpenAI configuration")
        # You might want to exit here or handle the error differently

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

class ConnectionManager:
    def __init__(self, max_connections: int = 100, timeout: int = 600):
        self.active_connections: Dict[str, WebSocket] = {}  # Change to dict for better tracking
        self.max_connections = max_connections
        self.timeout = timeout
        self.connection_times: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> bool:
        client_id = f"{websocket.client.host}:{websocket.client.port}"
        
        async with self._lock:
            # Check if this client already has a connection
            if client_id in self.active_connections:
                logger.warning(f"Client {client_id} already has an active connection")
                try:
                    await self.active_connections[client_id].close()
                except Exception:
                    pass
                del self.active_connections[client_id]
                del self.connection_times[client_id]

            # Check total connections
            if len(self.active_connections) >= self.max_connections:
                logger.warning(f"Maximum connection limit reached ({self.max_connections})")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False

            try:
                await websocket.accept()
                self.active_connections[client_id] = websocket
                self.connection_times[client_id] = datetime.now()
                logger.info(f"Client {client_id} connected. Active connections: {len(self.active_connections)}")
                
                if self._cleanup_task is None or self._cleanup_task.done():
                    self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                
                return True
            except Exception as e:
                logger.error(f"Error accepting connection from {client_id}: {e}")
                return False

    async def disconnect(self, websocket: WebSocket):
        client_id = f"{websocket.client.host}:{websocket.client.port}"
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                if client_id in self.connection_times:
                    del self.connection_times[client_id]
                logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
            
            with contextlib.suppress(Exception):
                await websocket.close()

    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                async with self._lock:
                    now = datetime.now()
                    stale_connections = []
                    
                    for client_id, ws in self.active_connections.items():
                        if not ws.client_state.connected:
                            stale_connections.append(client_id)
                        elif (now - self.connection_times[client_id]).total_seconds() > self.timeout:
                            stale_connections.append(client_id)
                    
                    for client_id in stale_connections:
                        if client_id in self.active_connections:
                            await self.disconnect(self.active_connections[client_id])
                            
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connection_info(self) -> dict:
        return {
            "total_connections": len(self.active_connections),
            "max_connections": self.max_connections,
            "clients": [
                {
                    "id": client_id,
                    "connected_at": self.connection_times[client_id].isoformat(),
                    "duration": (datetime.now() - self.connection_times[client_id]).total_seconds()
                }
                for client_id in self.active_connections
            ]
        }

# Initialize the connection manager
manager = ConnectionManager()

async def stream_generator(stream):
    try:
        async for chunk in stream:
            if chunk and chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"Error in stream_generator: {str(e)}")
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat functionality with proper stream handling"""
    try:
        if not await manager.connect(websocket):
            return

        while True:
            try:
                data = await websocket.receive_text()
                logger.info("Received WebSocket message")
                logger.debug(f"Message content: {data[:100]}...")
                
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
                
                try:
                    stream = await generate_chat_completion(
                        messages=messages,
                        max_tokens=chat_request.max_tokens,
                        temperature=chat_request.temperature,
                        stream=True
                    )
                    
                    async for content in stream_generator(stream):
                        await websocket.send_text(content)
                    
                except Exception as e:
                    error_msg = f"OpenAI API error: {str(e)}"
                    logger.error(error_msg)
                    logger.exception(e)
                    await websocket.send_text(f"Error: {str(e)}")
                    
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.exception(e)
                await websocket.send_text(f"Error: {str(e)}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        logger.exception(e)
    finally:
        await manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
