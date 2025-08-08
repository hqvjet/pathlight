import Cookies from 'js-cookie';

// =============================================================================
// 🍪 COOKIE UTILITIES
// =============================================================================

export interface CookieOptions {
  expires?: number | Date;
  path?: string;
  domain?: string;
  secure?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
  httpOnly?: boolean;
}

// Default cookie options for security
const DEFAULT_OPTIONS: CookieOptions = {
  secure: true,         // Only send over HTTPS
  sameSite: 'strict',   // CSRF protection
  path: '/',            // Available for entire app
};

// Token cookie options
const TOKEN_OPTIONS: CookieOptions = {
  ...DEFAULT_OPTIONS,
  expires: 7,           // 7 days default expiry
};

const SESSION_TOKEN_OPTIONS: CookieOptions = {
  ...DEFAULT_OPTIONS,
  // No expires = session cookie (deleted when browser closes)
};

export const cookieStorage = {
  // =============================================================================
  // 🔐 TOKEN MANAGEMENT
  // =============================================================================
  
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    
    // Try persistent token first, then session token
    return Cookies.get('auth_token') || Cookies.get('session_token') || null;
  },
  
  setToken: (token: string, remember: boolean = false): void => {
    if (typeof window === 'undefined') return;
    
    // Clear any existing tokens first
    cookieStorage.removeToken();
    
    if (remember) {
      // Set persistent token with 7 days expiry
      Cookies.set('auth_token', token, TOKEN_OPTIONS);
      Cookies.set('remember_me', 'true', TOKEN_OPTIONS);
    } else {
      // Set session token (expires when browser closes)
      Cookies.set('session_token', token, SESSION_TOKEN_OPTIONS);
      Cookies.remove('remember_me');
    }
  },
  
  removeToken: (): void => {
    if (typeof window === 'undefined') return;
    
    // Remove all possible token cookies
    Cookies.remove('auth_token', { path: '/' });
    Cookies.remove('session_token', { path: '/' });
    Cookies.remove('remember_me', { path: '/' });
  },
  
  isRemembered: (): boolean => {
    if (typeof window === 'undefined') return false;
    return Cookies.get('remember_me') === 'true';
  },
  
  // =============================================================================
  // 📧 EMAIL VERIFICATION
  // =============================================================================
  
  getPendingEmail: (): string | null => {
    if (typeof window === 'undefined') return null;
    return Cookies.get('pending_email') || null;
  },
  
  setPendingEmail: (email: string): void => {
    if (typeof window === 'undefined') return;
    // Set with 1 hour expiry for email verification
    Cookies.set('pending_email', email, {
      ...DEFAULT_OPTIONS,
      expires: 1/24, // 1 hour
    });
  },
  
  removePendingEmail: (): void => {
    if (typeof window === 'undefined') return;
    Cookies.remove('pending_email', { path: '/' });
  },
  
  // =============================================================================
  // 🔧 GENERIC COOKIE OPERATIONS
  // =============================================================================
  
  get: (key: string): string | null => {
    if (typeof window === 'undefined') return null;
    return Cookies.get(key) || null;
  },
  
  set: (key: string, value: string, options?: CookieOptions): void => {
    if (typeof window === 'undefined') return;
    Cookies.set(key, value, { ...DEFAULT_OPTIONS, ...options });
  },
  
  remove: (key: string): void => {
    if (typeof window === 'undefined') return;
    Cookies.remove(key, { path: '/' });
  },
  
  clear: (): void => {
    if (typeof window === 'undefined') return;
    
    // Get all cookies and remove them
    const allCookies = Cookies.get();
    Object.keys(allCookies).forEach(cookieName => {
      Cookies.remove(cookieName, { path: '/' });
    });
  },
  
  // =============================================================================
  // 🛡️ SECURITY UTILITIES
  // =============================================================================
  
  // Check if cookies are enabled
  isCookieEnabled: (): boolean => {
    if (typeof window === 'undefined') return false;
    
    try {
      const testKey = '__cookie_test__';
      Cookies.set(testKey, 'test');
      const result = Cookies.get(testKey) === 'test';
      Cookies.remove(testKey);
      return result;
    } catch {
      return false;
    }
  },
  
  // Get token expiry (for persistent tokens)
  getTokenExpiry: (): Date | null => {
    if (typeof window === 'undefined') return null;
    
    const token = Cookies.get('auth_token');
    if (!token) return null;
    
    // Parse JWT to get expiry (basic implementation)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp ? new Date(payload.exp * 1000) : null;
    } catch {
      return null;
    }
  },
  
  // Check if token is about to expire (within 5 minutes)
  isTokenExpiringSoon: (): boolean => {
    const expiry = cookieStorage.getTokenExpiry();
    if (!expiry) return false;
    
    const fiveMinutesFromNow = new Date(Date.now() + 5 * 60 * 1000);
    return expiry <= fiveMinutesFromNow;
  },
};

// =============================================================================
// 🔒 DEVELOPMENT MODE ADJUSTMENTS
// =============================================================================

// In development, we might not have HTTPS, so adjust settings
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  DEFAULT_OPTIONS.secure = false;
  TOKEN_OPTIONS.secure = false;
  SESSION_TOKEN_OPTIONS.secure = false;
}
