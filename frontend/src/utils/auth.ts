import { storage } from './api';

export const authUtils = {
  logout: (): void => {
    storage.removeToken();
    
    if (typeof window !== 'undefined') {
      window.location.href = '/signin';
    }
  },

  isAuthenticated: (): boolean => {
    return !!storage.getToken();
  },

  handleSessionExpiry: (): void => {
    // Chỉ xóa session token, không xóa persistent token
    if (typeof window !== 'undefined' && !storage.isRemembered()) {
      sessionStorage.removeItem('token');
    }
  },

  handleBeforeUnload: (): void => {
    if (!storage.isRemembered()) {
      storage.removeToken();
    }
  }
};

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', authUtils.handleBeforeUnload);
  
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && !storage.isRemembered()) {
      sessionStorage.removeItem('token');
    }
  });
}
