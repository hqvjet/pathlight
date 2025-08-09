import { storage } from './api';

export const authUtils = {
  logout: (): void => {
    storage.removeToken();
    
    if (typeof window !== 'undefined') {
      window.location.replace('/auth/signin');
    }
  },

  isAuthenticated: (): boolean => {
    return !!storage.getToken();
  },

  // Check if token is about to expire and needs refresh
  shouldRefreshToken: (): boolean => {
    return storage.isTokenExpiringSoon?.() || false;
  },

  // Enhanced session management for cookies
  handleSessionExpiry: (): void => {
    // Only remove token if it's a session token (not remembered)
    if (typeof window !== 'undefined' && !storage.isRemembered()) {
      storage.removeToken();
    }
  },

  // Check if cookies are supported
  checkCookieSupport: (): boolean => {
    return storage.isCookieEnabled?.() || false;
  },
};
