import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Loader, Bold, Italic, Code
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_API_URL || 'https://ludus-chat-backend.azurewebsites.net';
const WS_URL = process.env.REACT_APP_WS_URL || 'wss://ludus-chat-backend.azurewebsites.net/ws';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const MessageContent: React.FC<{ content: string }> = ({ content }) => {
  const formatText = (text: string): string => {
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-800 text-gray-200 px-1 rounded">$1</code>');
    return text;
  };

  return (
    <div 
      className="prose prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: formatText(content) }}
    />
  );
};

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connectWebSocket = useCallback(() => {
    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    // Don't create a new connection if one already exists and is open
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    // Maximum number of reconnection attempts
    const MAX_RECONNECT_ATTEMPTS = 5;
    
    try {
      console.log('Connecting to WebSocket...', WS_URL);
      const wsInstance = new WebSocket(WS_URL);
      
      wsInstance.onopen = () => {
        console.log('WebSocket connected successfully');
        setWsConnected(true);
        setReconnectAttempt(0); // Reset reconnection attempts on successful connection
      };

      wsInstance.onclose = (event) => {
        console.log('WebSocket disconnected', event);
        setWsConnected(false);
        ws.current = null;

        // Only attempt reconnection if not intentionally closed and within max attempts
        if (!event.wasClean && reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
          const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttempt), 10000);
          console.log(`Attempting to reconnect in ${backoffDelay}ms... (Attempt ${reconnectAttempt + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempt(prev => prev + 1);
            connectWebSocket();
          }, backoffDelay);
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
              newMessages[newMessages.length - 1].content += event.data;
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
    }
  }, [reconnectAttempt]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatText = (formatType: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = input.substring(start, end);
    let formattedText = '';

    switch (formatType) {
      case 'bold':
        formattedText = `**${selectedText}**`;
        break;
      case 'italic':
        formattedText = `*${selectedText}*`;
        break;
      case 'code':
        formattedText = `\`${selectedText}\``;
        break;
      default:
        return;
    }

    const newText = input.substring(0, start) + formattedText + input.substring(end);
    setInput(newText);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

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
        max_tokens: 800,
        temperature: 0.7
      };

      if (wsConnected && ws.current?.readyState === WebSocket.OPEN) {
        console.log('Sending message via WebSocket');
        ws.current.send(JSON.stringify(requestBody));
      } else {
        console.log('Sending message via HTTP');
        const response = await fetch(`${BACKEND_URL}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-4 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">Ludus Chat Assistant</h1>
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {wsConnected ? 'Connected' : 'Disconnected'}
          {reconnectAttempt > 0 && !wsConnected && ` (Reconnecting... Attempt ${reconnectAttempt})`}
        </div>
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
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white shadow-sm'
              }`}
            >
              <MessageContent content={message.content} />
              <div className="text-xs mt-2 text-gray-500">
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
        <div className="border rounded-lg mb-4">
          <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-gray-50">
            <button
              onClick={() => formatText('bold')}
              className="p-2 rounded hover:bg-gray-100"
              title="Bold"
            >
              <Bold className="w-4 h-4" />
            </button>
            <button
              onClick={() => formatText('italic')}
              className="p-2 rounded hover:bg-gray-100"
              title="Italic"
            >
              <Italic className="w-4 h-4" />
            </button>
            <button
              onClick={() => formatText('code')}
              className="p-2 rounded hover:bg-gray-100"
              title="Code"
            >
              <Code className="w-4 h-4" />
            </button>
          </div>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Type your message... (Shift + Enter for new line)"
            className="w-full p-3 focus:outline-none min-h-[100px] resize-none"
            rows={4}
          />
        </div>
        <div className="flex justify-end">
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