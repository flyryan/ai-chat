/**
 * Get environment variable with type checking and default value
 * @param key - Environment variable key (without REACT_APP_ prefix)
 * @param defaultValue - Optional default value if environment variable is not set
 * @returns The environment variable value or default value
 */
export const getEnvValue = (key: string, defaultValue?: string): string => {
    const fullKey = `REACT_APP_${key}`;
    const value = process.env[fullKey];
    
    if (value === undefined) {
        if (defaultValue === undefined) {
            console.error(`Environment variable ${fullKey} is not defined`);
            return '';
        }
        return defaultValue;
    }
    
    return value;
};

/**
 * Parse boolean environment variable
 * @param key - Environment variable key (without REACT_APP_ prefix)
 * @param defaultValue - Default value if environment variable is not set
 * @returns Parsed boolean value
 */
export const getEnvBoolean = (key: string, defaultValue = false): boolean => {
    const value = getEnvValue(key, String(defaultValue));
    return value.toLowerCase() === 'true';
};

/**
 * Parse number environment variable
 * @param key - Environment variable key (without REACT_APP_ prefix)
 * @param defaultValue - Default value if environment variable is not set
 * @returns Parsed number value
 */
export const getEnvNumber = (key: string, defaultValue: number): number => {
    const value = getEnvValue(key, String(defaultValue));
    const parsed = Number(value);
    return isNaN(parsed) ? defaultValue : parsed;
};
