'use client';

import { useState, useEffect } from 'react';
import { storage } from '@/utils/api';
import { authUtils } from '@/utils/auth';

function tokenExpired(token: string | null) {
  if (!token) return true;
  const parts = token.split('.');
  if (parts.length !== 3) return false; // opaque token
  try { const payload = JSON.parse(atob(parts[1].replace(/-/g,'+').replace(/_/g,'/'))); if (!payload.exp) return false; return payload.exp * 1000 <= Date.now(); } catch { return true; }
}

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isRemembered, setIsRemembered] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Kiểm tra authentication status khi component mount
    const checkAuth = () => {
      const token = storage.getToken();
      if (tokenExpired(token)) {
        storage.removeToken();
        setIsAuthenticated(false);
        setIsRemembered(false);
        setLoading(false);
        return;
      }
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
