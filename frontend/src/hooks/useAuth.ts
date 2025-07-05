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

    // Lắng nghe storage changes
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'token' || e.key === 'remember_me') {
        checkAuth();
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
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
