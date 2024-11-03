export interface Config {
  // Basic configuration
  APP_NAME: string;
  
  // API Configuration
  API_URL: string;
  WS_URL: string;
  
  // Chat Configuration
  MAX_RECONNECT_ATTEMPTS: number;
  DEFAULT_MAX_TOKENS: number;
  DEFAULT_TEMPERATURE: number;
  
  // UI Configuration
  MESSAGE_HISTORY_LIMIT: number;
  CODE_LANGUAGES: readonly string[];
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface WebSocketManagerOptions {
  url: string;
  maxReconnectAttempts: number;
  onMessage: (data: string) => void;
  onConnectionChange: (connected: boolean) => void;
  onError: (error: string) => void;
}
