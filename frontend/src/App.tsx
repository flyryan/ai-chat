import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, AlertTriangle } from 'lucide-react';
import { marked } from 'marked';
import MarkdownEditor from './components/MarkdownEditor';
import { config } from './config';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface ChatResponse {
  response: string;
  timestamp: string;
}

// Configure marked
const renderer = new marked.Renderer();

renderer.codespan = function(text: string) {
  // Remove only the outermost backticks if they exist
  text = text.replace(/^`|`$/g, '');
  return `<code class="inline-code">${text}</code>`;
};

marked.use({ renderer });

// HTTP fallback function
const sendMessageHttp = async (requestBody: any): Promise<ChatResponse> => {
  const url = `${config.API_URL}/chat`;
  console.log('Sending HTTP request to:', url);
  console.log('Request body:', requestBody);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

// WebSocket handling code
class WebSocketHandler {
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempt = 0;
  private options: {
    onMessage: (data: string) => void;
    onError: (message: string) => void;
  };

  constructor(options: { onMessage: (data: string) => void; onError: (message: string) => void }) {
    this.options = options;
  }

  private connect() {
    // WebSocket connection logic
  }

  private handleError(error: Event) {
    console.error('WebSocket error:', error);
    this.options.onError('Connection error');
  }

  private handleMessage(event: MessageEvent) {
    this.options.onMessage(event.data);
  }
}

const ConnectionStatus: React.FC<{ 
  wsConnected: boolean, 
  useHttpFallback: boolean 
}> = ({ 
  wsConnected, 
  useHttpFallback
}) => (
  <div className="flex items-center gap-2 text-sm">
    <span 
      className={`w-2 h-2 rounded-full ${
        wsConnected ? 'bg-green-500' : 'bg-red-500'
      }`} 
    />
    {useHttpFallback ? 'Using HTTP Mode' : 
     wsConnected ? 'Connected' : 'Disconnected'}
  </div>
);

interface WebSocketManagerOptions {
  url: string;
  maxReconnectAttempts: number;
  onMessage: (data: string) => void;
  onConnectionChange: (connected: boolean) => void;
  onError: (error: string) => void;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempt = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageQueue: string[] = [];
  private connecting = false;
  private options: WebSocketManagerOptions;
  private closedIntentionally = false;
  private lastConnectAttempt = 0;
  private static instance: WebSocketManager | null = null;
  
  private constructor(options: WebSocketManagerOptions) {
    this.options = options;
  }

  static getInstance(options: WebSocketManagerOptions): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager(options);
    }
    return WebSocketManager.instance;
  }

  connect() {
    const now = Date.now();
    const timeSinceLastAttempt = now - this.lastConnectAttempt;
    
    if (
      this.ws?.readyState === WebSocket.OPEN || 
      this.connecting ||
      timeSinceLastAttempt < 1000  // Prevent attempts more frequent than 1 second
    ) {
      return;
    }

    this.lastConnectAttempt = now;
    this.connecting = true;
    this.closedIntentionally = false;

    try {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }

      console.log('Connecting to WebSocket:', this.options.url);
      this.ws = new WebSocket(this.options.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);

    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.connecting = false;
      this.options.onError('Failed to create connection');
    }
  }

  private handleOpen() {
    console.log('WebSocket connected');
    this.connecting = false;
    this.reconnectAttempt = 0;
    this.options.onConnectionChange(true);
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) this.send(message);
    }
  }

  private handleClose() {
    console.log('WebSocket closed');
    this.options.onConnectionChange(false);
    this.connecting = false;
    this.ws = null;

    if (!this.closedIntentionally && this.reconnectAttempt < this.options.maxReconnectAttempts) {
      const backoffDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempt), 10000);
      console.log(`Reconnecting in ${backoffDelay}ms (attempt ${this.reconnectAttempt + 1})`);
      
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
      }
      
      this.reconnectTimeout = setTimeout(() => {
        this.reconnectAttempt++;
        this.connect();
      }, backoffDelay);
    }
  }

  private handleError(error: Event) {
    console.error('WebSocket error:', error);
    this.options.onError('Connection error');
  }

  private handleMessage(event: MessageEvent) {
    this.options.onMessage(event.data);
  }

  send(message: string): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
      return true;
    } else if (this.connecting && this.messageQueue.length < 10) { // Limit queued messages
      this.messageQueue.push(message);
      return true;
    }
    return false;
  }

  disconnect() {
    this.closedIntentionally = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageQueue = [];
    this.connecting = false;
    this.reconnectAttempt = 0;
    WebSocketManager.instance = null;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial health check
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${config.API_URL}/health`, {
          credentials: 'include',
          mode: 'cors',
        });
        
        if (!response.ok) {
          throw new Error(`Health check failed: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Health check response:', data);
        setInitError(null);
      } catch (error) {
        console.error('Health check error:', error);
        setInitError('Could not connect to chat service. Please try again later.');
      }
    };

    checkHealth();
  }, []);

  // WebSocket connection effect
  useEffect(() => {
    if (!useHttpFallback) {
      const manager = WebSocketManager.getInstance({
        url: config.WS_URL,
        maxReconnectAttempts: config.MAX_RECONNECT_ATTEMPTS,
        onMessage: (data: string) => {
          setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant') {
              const lastMessage = { ...newMessages[newMessages.length - 1] };
              lastMessage.content += data;
              newMessages[newMessages.length - 1] = lastMessage;
            } else {
              newMessages.push({
                role: 'assistant',
                content: data,
                timestamp: new Date().toISOString()
              });
            }
            return newMessages;
          });
        },
        onConnectionChange: (connected: boolean) => {
          setWsConnected(connected);
          if (connected) {
            setError(null);
            setUseHttpFallback(false);
          }
        },
        onError: (errorMessage: string) => {
          setError(errorMessage);
        }
      });
      manager.connect();

      return () => {
        manager.disconnect();
      };
    }
  }, [useHttpFallback]);

  // Scroll to bottom effect
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setError(null);

    const newMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    try {
      setMessages(prev => [...prev, newMessage]);
      setInput('');
      setIsLoading(true);

      const requestBody = {
        messages: [...messages, newMessage].map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        })),
        max_tokens: config.DEFAULT_MAX_TOKENS,
        temperature: config.DEFAULT_TEMPERATURE
      };

      if (!useHttpFallback && WebSocketManager.getInstance({
        url: config.WS_URL,
        maxReconnectAttempts: config.MAX_RECONNECT_ATTEMPTS,
        onMessage: () => {},
        onConnectionChange: () => {},
        onError: () => {}
      }).isConnected()) {
        const sent = WebSocketManager.getInstance({
          url: config.WS_URL,
          maxReconnectAttempts: config.MAX_RECONNECT_ATTEMPTS,
          onMessage: () => {},
          onConnectionChange: () => {},
          onError: () => {}
        }).send(JSON.stringify(requestBody));
        if (!sent) {
          throw new Error("Failed to send message via WebSocket");
        }
      } else {
        const data = await sendMessageHttp(requestBody);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        }]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message. Please try again.');
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (content: string) => {
    console.log('Raw content:', JSON.stringify(content));
    const html = marked(content);
    console.log('Final HTML:', html);
    return html;
  };

  if (initError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
          <div className="flex items-center gap-2 text-red-600 mb-4">
            <AlertTriangle className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Connection Error</h2>
          </div>
          <p className="text-gray-600 mb-4">{initError}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-4 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">{config.APP_NAME}</h1>
        <ConnectionStatus 
          wsConnected={wsConnected}
          useHttpFallback={useHttpFallback}
        />
        {error && (
          <div className="mt-2 text-sm text-red-600">
            {error}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-[90%] w-full mx-auto lg:max-w-[1200px]">
        {messages.slice(-config.MESSAGE_HISTORY_LIMIT).map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-6 shadow-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white ml-auto'
                  : 'bg-white text-gray-900 mr-auto'
              }`}
            >
              <div 
                className={`prose max-w-none ${
                  message.role === 'user' 
                    ? 'prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white prose-code:text-white' 
                    : 'prose-p:text-gray-900 prose-headings:text-gray-900 prose-strong:text-gray-900'
                }`}
                dangerouslySetInnerHTML={{ 
                  __html: renderMessage(message.content)
                }} 
              />
              <div className={`text-xs mt-2 text-opacity-75 ${
                message.role === 'user' ? 'text-gray-200' : 'text-gray-500'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <Loader className="w-6 h-6 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white shadow-lg">
        <MarkdownEditor
          value={input}
          onChange={setInput}
          onSubmit={sendMessage}
          placeholder="Type your message... (Shift + Enter for new line)"
          disabled={isLoading}
        />
        <div className="flex justify-end mt-4">
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 
                     flex items-center gap-2"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}