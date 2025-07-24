/**
 * =============================================================================
 * 🌍 PATHLIGHT FRONTEND - CONFIGURATION INDEX
 * =============================================================================
 * Central export for all configuration modules
 */

// Export environment configuration
export * from './env';

// Re-export with better naming
export { 
  API_CONFIG as apiConfig,
  AUTH_CONFIG as authConfig,
  APP_CONFIG as appConfig,
  FEATURE_FLAGS as featureFlags,
  ANALYTICS_CONFIG as analyticsConfig,
  getEnvironmentInfo
} from './env';
