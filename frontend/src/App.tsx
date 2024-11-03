import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Loader, Copy, Check, Bold, Italic, Code, List, 
  ListOrdered, Terminal 
} from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface CodeBlockProps {
  language?: string;
  children: string;
}

interface MessageContentProps {
  content: string;
}

interface FormatButtonProps {
  icon: React.ElementType;
  label: string;
  onClick: () => void;
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const CodeBlock: React.FC<CodeBlockProps> = ({ language = 'text', children }) => {
    const [copied, setCopied] = useState(false);

    const copyCode = () => {
      navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    return (
      <div className="relative rounded-lg overflow-hidden my-2 font-mono">
        <div className="bg-gray-800 text-gray-200 px-4 py-1 text-sm flex justify-between items-center">
          <span>{language}</span>
          <button
            onClick={copyCode}
            className="p-1 rounded hover:bg-gray-700 transition-colors"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
        <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto">
          <code>{children}</code>
        </pre>
      </div>
    );
  };

  const MessageContent: React.FC<MessageContentProps> = ({ content }) => {
    interface Segment {
      type: 'text' | 'code';
      content: string;
      language?: string;
    }

    const parseContent = (text: string): Segment[] => {
      const segments: Segment[] = [];
      let currentIndex = 0;
      
      const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
      let match: RegExpExecArray | null;
      
      while ((match = codeBlockRegex.exec(text)) !== null) {
        if (match.index > currentIndex) {
          segments.push({
            type: 'text',
            content: text.slice(currentIndex, match.index)
          });
        }
        
        segments.push({
          type: 'code',
          language: match[1] || 'text',
          content: match[2].trim()
        });
        
        currentIndex = match.index + match[0].length;
      }
      
      if (currentIndex < text.length) {
        segments.push({
          type: 'text',
          content: text.slice(currentIndex)
        });
      }
      
      return segments;
    };

    const formatText = (text: string): string => {
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
      text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-800 text-gray-200 px-1 rounded">$1</code>');
      text = text.replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>');
      text = text.replace(/^\d+\. (.+)$/gm, '<li class="ml-4">$1</li>');
      return text;
    };

    const segments = parseContent(content);

    return (
      <div className="space-y-2">
        {segments.map((segment, index) => {
          if (segment.type === 'code') {
            return (
              <CodeBlock key={index} language={segment.language}>
                {segment.content}
              </CodeBlock>
            );
          }

          const formattedHtml = formatText(segment.content);
          return (
            <div 
              key={index} 
              className="prose prose-invert max-w-none"
              dangerouslySetInnerHTML={{ 
                __html: formattedHtml
              }}
            />
          );
        })}
      </div>
    );
  };

  const FormatButton: React.FC<FormatButtonProps> = ({ icon: Icon, label, onClick }) => (
    <button
      onClick={onClick}
      className="p-2 rounded hover:bg-gray-100 flex items-center gap-1 text-gray-700"
      title={label}
    >
      <Icon className="w-4 h-4" />
      <span className="text-sm hidden sm:inline">{label}</span>
    </button>
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const connectWebSocket = useCallback(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws');
    
    ws.current.onopen = () => {
      setWsConnected(true);
    };

    ws.current.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };

    ws.current.onmessage = (event) => {
      const data = event.data;
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant') {
          newMessages[newMessages.length - 1].content += data;
        } else {
          newMessages.push({
            role: 'assistant',
            content: data,
            timestamp: new Date().toISOString()
          });
        }
        return newMessages;
      });
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket]);

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
      case 'inlineCode':
        formattedText = `\`${selectedText}\``;
        break;
      case 'codeBlock':
        formattedText = `\`\`\`\n${selectedText}\n\`\`\``;
        break;
      case 'bulletList':
        formattedText = selectedText
          .split('\n')
          .map(line => `- ${line}`)
          .join('\n');
        break;
      case 'numberedList':
        formattedText = selectedText
          .split('\n')
          .map((line, i) => `${i + 1}. ${line}`)
          .join('\n');
        break;
      default:
        return;
    }

    const newText = input.substring(0, start) + formattedText + input.substring(end);
    setInput(newText);

    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + formattedText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

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
      ws.current.send(JSON.stringify({
        messages: [...messages, newMessage],
        max_tokens: 800,
        temperature: 0.7
      }));
    } else {
      try {
        const response = await fetch('http://localhost:8000/chat', {
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
        console.error('Error:', error);
      }
    }
    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-4 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">Ludus Chat Assistant</h1>
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {wsConnected ? 'Connected' : 'Disconnected'}
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
            <FormatButton
              icon={Bold}
              label="Bold"
              onClick={() => formatText('bold')}
            />
            <FormatButton
              icon={Italic}
              label="Italic"
              onClick={() => formatText('italic')}
            />
            <FormatButton
              icon={Code}
              label="Inline Code"
              onClick={() => formatText('inlineCode')}
            />
            <FormatButton
              icon={Terminal}
              label="Code Block"
              onClick={() => formatText('codeBlock')}
            />
            <FormatButton
              icon={List}
              label="Bullet List"
              onClick={() => formatText('bulletList')}
            />
            <FormatButton
              icon={ListOrdered}
              label="Numbered List"
              onClick={() => formatText('numberedList')}
            />
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
            className="w-full p-3 focus:outline-none focus:ring-0 border-none rounded-b-lg min-h-[2.5rem] max-h-48 resize-y"
            rows={3}
          />
        </div>
        <div className="flex justify-end">
          <button
            onClick={sendMessage}
            disabled={isLoading}
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
