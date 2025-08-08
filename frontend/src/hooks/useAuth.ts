'use client';

import { useState, useEffect } from 'react';
import { storage } from '@/utils/api';
import { authUtils } from '@/utils/auth';

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isRemembered, setIsRemembered] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Kiểm tra authentication status khi component mount
    const checkAuth = () => {
      const token = storage.getToken();
      const remembered = storage.isRemembered();
      
      setIsAuthenticated(!!token);
      setIsRemembered(remembered);
      setLoading(false);
    };

    checkAuth();

    // Check auth status periodically (cookies don't trigger storage events)
    const interval = setInterval(checkAuth, 60000); // Check every minute

    // Also check when tab becomes visible again
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkAuth();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const logout = () => {
    authUtils.logout();
    setIsAuthenticated(false);
    setIsRemembered(false);
  };

  return {
    isAuthenticated,
    isRemembered,
    loading,
    logout
  };
};
