import { getEnvValue } from './utils/env';

interface Config {
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

const getEnvVar = (key: string, defaultValue?: string): string => {
  // Check process.env first
  const value = process.env[`REACT_APP_${key}`] ?? defaultValue;
  if (value === undefined) {
    console.error(`Environment variable REACT_APP_${key} is not defined`);
    return defaultValue || '';
  }
  return value;
};

const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeout = 5000): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      mode: 'cors',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

// Add fetchWithConfig function
export const fetchWithConfig = async (url: string, options: RequestInit = {}): Promise<Response> => {
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

// Create the configuration object
export const config: Config = {
  // Basic configuration
  APP_NAME: getEnvVar('APP_NAME', 'AI Chat Assistant'),
  
  // API Configuration
  API_URL: getEnvVar('API_URL', window.location.protocol === 'https:' 
    ? 'https://localhost:8000' 
    : 'http://localhost:8000'
  ),
  WS_URL: getEnvVar('WS_URL', window.location.protocol === 'https:' 
    ? 'wss://localhost:8000/ws' 
    : 'ws://localhost:8000/ws'
  ),
  
  // Chat Configuration
  MAX_RECONNECT_ATTEMPTS: parseInt(getEnvVar('MAX_RECONNECT_ATTEMPTS', '5')),
  DEFAULT_MAX_TOKENS: parseInt(getEnvVar('DEFAULT_MAX_TOKENS', '4000')),
  DEFAULT_TEMPERATURE: parseFloat(getEnvVar('DEFAULT_TEMPERATURE', '0.7')),
  
  // UI Configuration
  MESSAGE_HISTORY_LIMIT: parseInt(getEnvVar('MESSAGE_HISTORY_LIMIT', '100')),
  CODE_LANGUAGES: [
    'python',
    'javascript',
    'typescript',
    'bash',
    'json',
    'html',
    'css',
    'sql',
    'yaml',
    'markdown',
    'plaintext'
  ] as const
};

// Add health check function
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetchWithTimeout(`${config.API_URL}/health`);
    if (!response.ok) {
      console.error('Health check failed:', response.status);
      return false;
    }
    const data = await response.json();
    console.log('Health check response:', data);
    return true;
  } catch (error) {
    console.error('Health check error:', error);
    return false;
  }
};

// Add WebSocket check function
export const checkWebSocketConnection = async (): Promise<boolean> => {
  return new Promise((resolve) => {
    try {
      const ws = new WebSocket(config.WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket test connection successful');
        ws.close();
        resolve(true);
      };

      ws.onerror = (error) => {
        console.error('WebSocket test connection failed:', error);
        resolve(false);
      };

      // Timeout after 5 seconds
      setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          resolve(false);
        }
      }, 5000);
    } catch (error) {
      console.error('WebSocket test error:', error);
      resolve(false);
    }
  });
};

// Log configuration in development
if (process.env.NODE_ENV !== 'production') {
  console.log('Development Configuration:', {
    APP_NAME: config.APP_NAME,
    API_URL: config.API_URL,
    WS_URL: config.WS_URL,
  });
}

// Log configuration in production (without sensitive data)
if (process.env.NODE_ENV === 'production') {
  console.log('Frontend Configuration:', {
    APP_NAME: config.APP_NAME,
    API_URL: config.API_URL,
    WS_URL: config.WS_URL,
    environment: process.env.NODE_ENV
  });
}

// Validate configuration
const validateConfig = () => {
  const requiredFields = [
    'APP_NAME',
    'API_URL',
    'WS_URL'
  ];

  const missingFields = requiredFields.filter(field => !config[field as keyof Config]);
  
  if (missingFields.length > 0) {
    console.error('Missing required configuration fields:', missingFields);
  }

  // Validate URLs
  try {
    new URL(config.API_URL);
    new URL(config.WS_URL);
  } catch (error) {
    console.error('Invalid URL in configuration:', error);
  }

  // Validate numeric values
  if (config.MAX_RECONNECT_ATTEMPTS < 1) {
    console.error('MAX_RECONNECT_ATTEMPTS must be greater than 0');
  }
  if (config.DEFAULT_MAX_TOKENS < 1) {
    console.error('DEFAULT_MAX_TOKENS must be greater than 0');
  }
  if (config.DEFAULT_TEMPERATURE < 0 || config.DEFAULT_TEMPERATURE > 1) {
    console.error('DEFAULT_TEMPERATURE must be between 0 and 1');
  }
  if (config.MESSAGE_HISTORY_LIMIT < 1) {
    console.error('MESSAGE_HISTORY_LIMIT must be greater than 0');
  }
};

// Run validation
validateConfig();

export default config;