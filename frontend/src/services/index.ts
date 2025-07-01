/**
 * =============================================================================
 * 🔧 PATHLIGHT FRONTEND - SERVICES INDEX
 * =============================================================================
 * Central export for all service modules
 */

// Import all services
import authService from './auth.service';
import userService from './user.service';

// Export all services
export { default as authService } from './auth.service';
export { default as userService } from './user.service';

// Export types from services
export type * from './auth.service';
export type * from './user.service';

// Re-export with better naming
export { 
  authService as auth,
  userService as user,
};

// Utility to get all services
export const services = {
  auth: authService,
  user: userService,
} as const;

export default services;
