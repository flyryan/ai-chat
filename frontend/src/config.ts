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
  const value = process.env[`REACT_APP_${key}`] ?? defaultValue;
  if (value === undefined) {
    throw new Error(`Environment variable REACT_APP_${key} is not defined`);
  }
  return value;
};

export const config: Config = {
  // Basic configuration
  APP_NAME: getEnvVar('APP_NAME', 'AI Chat Assistant'),
  
  // API Configuration
  API_URL: getEnvVar('API_URL', 'http://localhost:8000'),
  WS_URL: getEnvVar('WS_URL', 'ws://localhost:8000/ws'),
  
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

export default config;
