import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader, AlertTriangle } from 'lucide-react';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';
import { marked } from 'marked';
import MarkdownEditor from './components/MarkdownEditor';
import { config } from './config';

// Configure marked to use Prism
marked.setOptions({
  highlight: function(code, lang) {
    if (Prism.languages[lang]) {
      return Prism.highlight(code, Prism.languages[lang], lang);
    }
    return code;
  }
});

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

const fetchWithCreds = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const defaultOptions: RequestInit = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    mode: 'cors',
  };

  const response = await fetch(url, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response;
};

const ConnectionStatus: React.FC<{ wsConnected: boolean, useHttpFallback: boolean, reconnectAttempt: number }> = ({ 
  wsConnected, 
  useHttpFallback, 
  reconnectAttempt 
}) => (
  <div className="flex items-center gap-2 text-sm">
    <span 
      className={`w-2 h-2 rounded-full ${
        wsConnected ? 'bg-green-500' : 'bg-red-500'
      }`} 
    />
    {useHttpFallback ? 'Using HTTP Mode' : 
     wsConnected ? 'Connected' : 
     reconnectAttempt > 0 ? `Reconnecting... ${reconnectAttempt}/${config.MAX_RECONNECT_ATTEMPTS}` :
     'Disconnected'}
  </div>
);

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connectWebSocket = useCallback(() => {
    if (reconnectAttempt >= config.MAX_RECONNECT_ATTEMPTS) {
      setUseHttpFallback(true);
      setWsConnected(false);
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      console.log('Connecting to WebSocket:', config.WS_URL);
      const wsInstance = new WebSocket(config.WS_URL);
      
      wsInstance.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
        setUseHttpFallback(false);
        setReconnectAttempt(0);
        setError(null);
      };

      wsInstance.onclose = () => {
        console.log('WebSocket closed');
        setWsConnected(false);
        ws.current = null;
    
        if (reconnectAttempt < config.MAX_RECONNECT_ATTEMPTS) {
          const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttempt), 10000);
          setReconnectAttempt(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, backoffDelay);
        } else {
          setUseHttpFallback(true);
        }
      };

      wsInstance.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      wsInstance.onmessage = (event) => {
        try {
          setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant') {
              const lastMessage = { ...newMessages[newMessages.length - 1] };
              lastMessage.content += event.data;
              newMessages[newMessages.length - 1] = lastMessage;
            } else {
              newMessages.push({
                role: 'assistant',
                content: event.data,
                timestamp: new Date().toISOString()
              });
            }
            return newMessages;
          });
        } catch (error) {
          console.error('Error processing message:', error);
          setError('Error processing message');
        }
      };

      ws.current = wsInstance;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setWsConnected(false);
      setUseHttpFallback(true);
    }
  }, [reconnectAttempt]);

  const sendMessageHttp = async (requestBody: any) => {
    const response = await fetchWithCreds(`${config.API_URL}/chat`, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });

    return response.json();
  };

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

      if (!useHttpFallback && wsConnected && ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(requestBody));
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
      setError('Failed to send message. Please try again.');
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!useHttpFallback) {
      connectWebSocket();
    }
  
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      ws.current?.close();
    };
  }, [connectWebSocket, useHttpFallback]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initial health check
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetchWithCreds(`${config.API_URL}/health`);
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
          reconnectAttempt={reconnectAttempt}
        />
        {error && (
          <div className="mt-2 text-sm text-red-600">
            {error}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.slice(-config.MESSAGE_HISTORY_LIMIT).map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white'
              }`}
            >
              <div 
                className="prose max-w-none" 
                dangerouslySetInnerHTML={{ 
                  __html: marked(message.content) 
                }} 
              />
              <div className={`text-xs mt-2 ${
                message.role === 'user' ? 'text-gray-200' : 'text-gray-500'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg p-4">
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
        <div className="flex justify-end mt-2">
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 
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