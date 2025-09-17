// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================

export const API_CONFIG = {
  // Primary backend base. Support legacy env name NEXT_PUBLIC_API_URL for backward compatibility.
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'https://xmicux090i.execute-api.ap-northeast-1.amazonaws.com/api',
  // If true we always call backend directly (not via Next.js route handlers) even for /api/user/* endpoints.
  DIRECT_BACKEND: (process.env.NEXT_PUBLIC_DIRECT_BACKEND || '').toLowerCase() === 'true',
  // Helpful for debugging which origin is actually used.
  get BACKEND_ORIGIN() { return this.BASE_URL; },
  get API_URL() {
    return this.BASE_URL;
  },
  get AUTH_SERVICE_URL() {
    return this.BASE_URL;
  },
  get USER_SERVICE_URL() {
    return this.BASE_URL;
  },
  get COURSE_SERVICE_URL() {
    return this.BASE_URL;
  },
  get QUIZ_SERVICE_URL() {
    return this.BASE_URL;
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
  NAME: process.env.NEXT_PUBLIC_APP_NAME || 'PathLight',
  VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || 'production',
  IS_DEVELOPMENT: process.env.NEXT_PUBLIC_ENVIRONMENT === 'development',
  IS_PRODUCTION: process.env.NEXT_PUBLIC_ENVIRONMENT !== 'development',
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
// 🔍 ENVIRONMENT INFO (Debug)
// =============================================================================

export const getEnvironmentInfo = () => ({
  NODE_ENV: process.env.NODE_ENV || 'production',
  NEXT_PUBLIC_ENVIRONMENT: APP_CONFIG.ENVIRONMENT,
  API_BASE_URL: API_CONFIG.BASE_URL,
  HAS_GOOGLE_CLIENT_ID: !!AUTH_CONFIG.GOOGLE_CLIENT_ID,
  FEATURE_FLAGS,
});

