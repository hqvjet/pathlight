/**
 * =============================================================================
 * 🌍 PATHLIGHT FRONTEND - ENVIRONMENT CONFIGURATION
 * =============================================================================
 * Centralized environment configuration with validation and type safety
 */

// Environment validation helper
const getEnvVar = (name: string, defaultValue?: string): string => {
  const value = process.env[name] || defaultValue;
  if (!value) {
    throw new Error(`Environment variable ${name} is required but not set`);
  }
  return value;
};

const getBooleanEnvVar = (name: string, defaultValue: boolean = false): boolean => {
  const value = process.env[name];
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
};

// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================
export const API_CONFIG = {
  BASE_URL: getEnvVar('NEXT_PUBLIC_API_BASE_URL', 'http://localhost:8000'),
  APP_URL: getEnvVar('NEXT_PUBLIC_APP_URL', 'http://localhost:3000'),
  
  // Service URLs with proper defaults
  AUTH_SERVICE_URL: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8001',
  USER_SERVICE_URL: process.env.NEXT_PUBLIC_USER_SERVICE_URL || 'http://localhost:8002',
  COURSE_SERVICE_URL: process.env.NEXT_PUBLIC_COURSE_SERVICE_URL || 'http://localhost:8003',
  QUIZ_SERVICE_URL: process.env.NEXT_PUBLIC_QUIZ_SERVICE_URL || 'http://localhost:8004',
} as const;

// =============================================================================
// 🔐 AUTHENTICATION CONFIGURATION
// =============================================================================
export const AUTH_CONFIG = {
  GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
  ENABLE_GOOGLE_AUTH: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_GOOGLE_AUTH', true),
  ENABLE_EMAIL_VERIFICATION: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_EMAIL_VERIFICATION', true),
  ENABLE_FORGOT_PASSWORD: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_FORGOT_PASSWORD', true),
} as const;

// =============================================================================
// 🛠️ APPLICATION CONFIGURATION
// =============================================================================
export const APP_CONFIG = {
  NAME: process.env.NEXT_PUBLIC_APP_NAME || 'PathLight',
  VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || 'development',
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
} as const;

// =============================================================================
// 🎨 FEATURE FLAGS
// =============================================================================
export const FEATURE_FLAGS = {
  ENABLE_GOOGLE_AUTH: AUTH_CONFIG.ENABLE_GOOGLE_AUTH,
  ENABLE_EMAIL_VERIFICATION: AUTH_CONFIG.ENABLE_EMAIL_VERIFICATION,
  ENABLE_FORGOT_PASSWORD: AUTH_CONFIG.ENABLE_FORGOT_PASSWORD,
} as const;

// =============================================================================
// 📊 ANALYTICS CONFIGURATION (Optional)
// =============================================================================
export const ANALYTICS_CONFIG = {
  GA_MEASUREMENT_ID: process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || '',
  SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN || '',
  ENABLE_ANALYTICS: !!process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID,
  ENABLE_ERROR_TRACKING: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
} as const;

// =============================================================================
// 🛡️ VALIDATION & DEBUGGING
// =============================================================================
export const validateEnvironment = (): void => {
  const requiredVars = [
    'NEXT_PUBLIC_API_BASE_URL',
    'NEXT_PUBLIC_APP_URL',
  ];

  const missingVars = requiredVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missingVars.join(', ')}\n` +
      'Please check your .env.local file or environment configuration.'
    );
  }

  // Warn about optional but recommended variables
  const recommendedVars = [
    { name: 'NEXT_PUBLIC_GOOGLE_CLIENT_ID', feature: 'Google OAuth' },
  ];

  recommendedVars.forEach(({ name, feature }) => {
    if (!process.env[name]) {
      console.warn(`⚠️  ${name} is not set - ${feature} will be disabled`);
    }
  });
};

// =============================================================================
// 🔍 ENVIRONMENT INFO (Debug)
// =============================================================================
export const getEnvironmentInfo = () => ({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_ENVIRONMENT: APP_CONFIG.ENVIRONMENT,
  API_BASE_URL: API_CONFIG.BASE_URL,
  APP_URL: API_CONFIG.APP_URL,
  HAS_GOOGLE_CLIENT_ID: !!AUTH_CONFIG.GOOGLE_CLIENT_ID,
  FEATURE_FLAGS,
});

// Auto-validate in development
if (APP_CONFIG.IS_DEVELOPMENT && typeof window === 'undefined') {
  try {
    validateEnvironment();
    console.log('✅ Environment validation passed');
    console.log('🌍 Environment Info:', getEnvironmentInfo());
  } catch (error) {
    console.error('❌ Environment validation failed:', error);
  }
}
