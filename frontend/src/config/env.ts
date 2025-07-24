// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================

export const API_CONFIG = {
  BASE_URL: 'http://localhost',
  APP_PORT: 3000,
  AUTH_SERVICE_PORT: 8001,
  USER_SERVICE_PORT: 8002,
  COURSE_SERVICE_PORT: 8003,
  QUIZ_SERVICE_PORT: 8004,
  get APP_URL() {
    return `${this.BASE_URL}:${this.APP_PORT}`;
  },
  get AUTH_SERVICE_URL() {
    return `${this.BASE_URL}:${this.AUTH_SERVICE_PORT}`;
  },
  get USER_SERVICE_URL() {
    return `${this.BASE_URL}:${this.USER_SERVICE_PORT}`;
  },
  get COURSE_SERVICE_URL() {
    return `${this.BASE_URL}:${this.COURSE_SERVICE_PORT}`;
  },
  get QUIZ_SERVICE_URL() {
    return `${this.BASE_URL}:${this.QUIZ_SERVICE_PORT}`;
  },
} as const;

// =============================================================================
// 🔐 AUTHENTICATION CONFIGURATION
// =============================================================================
export const AUTH_CONFIG = {
  GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
  ENABLE_GOOGLE_AUTH: true,
  ENABLE_EMAIL_VERIFICATION: true,
  ENABLE_FORGOT_PASSWORD: true,
} as const;

// =============================================================================
// 🛠️ APPLICATION CONFIGURATION
// =============================================================================
export const APP_CONFIG = {
  NAME: 'PathLight',
  VERSION: '1.0.0',
  ENVIRONMENT: 'development',
  IS_DEVELOPMENT: true,
  IS_PRODUCTION: false,
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
  GA_MEASUREMENT_ID: '',
  SENTRY_DSN: '',
  ENABLE_ANALYTICS: false,
  ENABLE_ERROR_TRACKING: false,
} as const;

// =============================================================================
// 🛡️ VALIDATION & DEBUGGING
// =============================================================================
// No validation needed, all config is hardcoded except GOOGLE_CLIENT_ID

// =============================================================================
// 🔍 ENVIRONMENT INFO (Debug)
// =============================================================================

export const getEnvironmentInfo = () => ({
  NODE_ENV: 'development',
  NEXT_PUBLIC_ENVIRONMENT: APP_CONFIG.ENVIRONMENT,
  API_BASE_URL: API_CONFIG.BASE_URL,
  APP_URL: API_CONFIG.APP_URL,
  AUTH_SERVICE_URL: API_CONFIG.AUTH_SERVICE_URL,
  USER_SERVICE_URL: API_CONFIG.USER_SERVICE_URL,
  COURSE_SERVICE_URL: API_CONFIG.COURSE_SERVICE_URL,
  QUIZ_SERVICE_URL: API_CONFIG.QUIZ_SERVICE_URL,
  HAS_GOOGLE_CLIENT_ID: !!AUTH_CONFIG.GOOGLE_CLIENT_ID,
  FEATURE_FLAGS,
});

// Auto-validate in development

