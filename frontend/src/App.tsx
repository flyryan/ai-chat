import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Loader, Copy, Check, Bold, Italic, Code, List, 
  ListOrdered, Terminal 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_API_URL || 'https://ludus-chat-backend.azurewebsites.net';
const WS_URL = process.env.REACT_APP_WS_URL || 'wss://ludus-chat-backend.azurewebsites.net/ws';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const connectWebSocket = useCallback(() => {
    console.log('Connecting to WebSocket...', WS_URL);
    const wsInstance = new WebSocket(WS_URL);
    
    wsInstance.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    wsInstance.onclose = (event) => {
      console.log('WebSocket disconnected', event);
      setWsConnected(false);
      // Attempt to reconnect after a delay
      setTimeout(connectWebSocket, 3000);
    };

    wsInstance.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsInstance.onmessage = (event) => {
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
    };

    ws.current = wsInstance;
  }, []);

  useEffect(() => {
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    setInput('');
    setIsLoading(true);

    if (wsConnected && ws.current) {
      console.log('Sending message via WebSocket');
      ws.current.send(JSON.stringify({
        messages: [...messages, newMessage],
        max_tokens: 800,
        temperature: 0.7
      }));
    } else {
      console.log('Sending message via HTTP');
      try {
        const response = await fetch(`${BACKEND_URL}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: [...messages, newMessage],
            max_tokens: 800,
            temperature: 0.7
          }),
        });

        const data = await response.json();
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        }]);
      } catch (error) {
        console.error('Error sending message:', error);
      }
    }
    setIsLoading(false);
  };

  // Rest of your component code (MessageContent, CodeBlock, etc.) remains the same...

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-4 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">Ludus Chat Assistant</h1>
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {wsConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {/* Rest of your JSX remains the same... */}
    </div>
  );
}