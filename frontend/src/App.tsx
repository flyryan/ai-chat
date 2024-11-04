import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader } from 'lucide-react';
import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import MarkdownEditor from './components/MarkdownEditor';

const BACKEND_URL = process.env.REACT_APP_API_URL || 'https://ludus-chat-backend.azurewebsites.net';
const WS_URL = process.env.REACT_APP_WS_URL || 'wss://ludus-chat-backend.azurewebsites.net/ws';
const MAX_RECONNECT_ATTEMPTS = 5;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const MessageContent: React.FC<{ content: string; role: Message['role'] }> = ({ content, role }) => {
  useEffect(() => {
    Prism.highlightAll();
  }, [content]);

  const renderer = new marked.Renderer();
  renderer.code = (code, language) => {
    const validLanguage = language && Prism.languages[language] ? language : 'text';
    const highlighted = Prism.highlight(
      code,
      Prism.languages[validLanguage] || Prism.languages.text,
      validLanguage
    );
    return `<pre class="bg-gray-900 rounded-lg p-4 my-3"><code class="language-${validLanguage}">${highlighted}</code></pre>`;
  };

  marked.setOptions({
    renderer,
    gfm: true,
    breaks: true,
    headerIds: true,
    headerPrefix: 'heading-'
  });

  const messageClasses = `prose max-w-none ${
    role === 'user' 
      ? 'prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white prose-code:text-white' 
      : 'prose-p:text-gray-900 prose-headings:text-gray-900 prose-strong:text-gray-900'
  }`;

  return (
    <div
      className={messageClasses}
      dangerouslySetInnerHTML={{ __html: marked(content) }}
    />
  );
};

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connectWebSocket = useCallback(() => {
    if (reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
      console.log('Max reconnection attempts reached, switching to HTTP fallback');
      setUseHttpFallback(true);
      setWsConnected(false);
      return;
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    try {
      console.log(`Connecting to WebSocket... Attempt ${reconnectAttempt + 1}/${MAX_RECONNECT_ATTEMPTS}`);
      const wsInstance = new WebSocket(WS_URL);
      
      wsInstance.onopen = () => {
        console.log('WebSocket connected successfully');
        setWsConnected(true);
        setUseHttpFallback(false);
        setReconnectAttempt(0);
      };

      wsInstance.onclose = (event) => {
        console.log('WebSocket disconnected', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          timestamp: new Date().toISOString()
        });
        
        setWsConnected(false);
        ws.current = null;
    
        // Log specific close codes
        switch (event.code) {
            case 1000:
                console.log("Normal closure");
                break;
            case 1006:
                console.log("Abnormal closure - potential server issue or network problem");
                break;
            case 1015:
                console.log("TLS handshake error");
                break;
            default:
                console.log(`Unknown close code: ${event.code}`);
        }
    
        if (!event.wasClean && reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
            const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttempt), 10000);
            console.log(`Scheduling reconnection in ${backoffDelay}ms...`);
            
            setReconnectAttempt(prev => prev + 1);
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, backoffDelay);
        } else {
            console.log('Switching to HTTP fallback mode');
            setUseHttpFallback(true);
        }
      };

      wsInstance.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsInstance.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
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
          console.error('Error processing WebSocket message:', error);
        }
      };

      ws.current = wsInstance;
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setWsConnected(false);
      setUseHttpFallback(true);
    }
  }, [reconnectAttempt]);

  const sendMessageHttp = async (requestBody: any) => {
    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for CORS
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('HTTP request failed:', error);
      throw error;
    }
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
        max_tokens: 4000,
        temperature: 0.7
      };

      if (!useHttpFallback && wsConnected && ws.current?.readyState === WebSocket.OPEN) {
        console.log('Sending message via WebSocket');
        ws.current.send(JSON.stringify(requestBody));
      } else {
        console.log('Sending message via HTTP');
        const data = await sendMessageHttp(requestBody);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      // Remove the user's message since it failed to send
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const connectWebSocket = () => {
      if (reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
        console.log('Max reconnection attempts reached, switching to HTTP fallback');
        setUseHttpFallback(true);
        setWsConnected(false);
        return;
      }
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
  
      try {
        console.log(`Connecting to WebSocket... Attempt ${reconnectAttempt + 1}/${MAX_RECONNECT_ATTEMPTS}`);
        const wsInstance = new WebSocket(WS_URL);
        
        wsInstance.onopen = () => {
          console.log('WebSocket connected successfully');
          setWsConnected(true);
          setUseHttpFallback(false);
          setReconnectAttempt(0);
        };
        wsInstance.onclose = (event) => {
          console.log('WebSocket disconnected', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
            timestamp: new Date().toISOString()
          });
          
          setWsConnected(false);
          ws.current = null;
      
          // Log specific close codes
          switch (event.code) {
              case 1000:
                  console.log("Normal closure");
                  break;
              case 1006:
                  console.log("Abnormal closure - potential server issue or network problem");
                  break;
              case 1015:
                  console.log("TLS handshake error");
                  break;
              default:
                  console.log(`Unknown close code: ${event.code}`);
          }
      
          if (!event.wasClean && reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
              const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttempt), 10000);
              console.log(`Scheduling reconnection in ${backoffDelay}ms...`);
              
              setReconnectAttempt(prev => prev + 1);
              reconnectTimeoutRef.current = setTimeout(connectWebSocket, backoffDelay);
          } else {
              console.log('Switching to HTTP fallback mode');
              setUseHttpFallback(true);
          }
        };
        wsInstance.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        wsInstance.onmessage = (event) => {
          try {
            console.log('WebSocket message received:', event.data);
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
            console.error('Error processing WebSocket message:', error);
          }
        };
        ws.current = wsInstance;
      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
      }
    };
  
    if (!useHttpFallback) {
      connectWebSocket();
    }
  
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket, useHttpFallback, reconnectAttempt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-4 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">Ludus Chat Assistant</h1>
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {useHttpFallback ? 'Using HTTP Mode' : 
           wsConnected ? 'Connected' : 
           reconnectAttempt > 0 ? `Disconnected (Reconnecting... Attempt ${reconnectAttempt}/${MAX_RECONNECT_ATTEMPTS})` :
           'Disconnected'}
        </div>
        {error && (
          <div className="mt-2 text-sm text-red-600">
            {error}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-3xl rounded-lg p-6 shadow-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-900'
              }`}
            >
              <MessageContent content={message.content} role={message.role} />
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
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center gap-2"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}