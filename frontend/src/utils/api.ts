import { API_CONFIG } from '../config/env';

// =============================================================================
// 🌐 API BASE CONFIGURATION
// =============================================================================
export const API_BASE = API_CONFIG.BASE_URL;

// =============================================================================
// 🔗 API ENDPOINTS
// =============================================================================
export const endpoints = {
  // Authentication endpoints
  signin: '/api/v1/signin',
  signup: '/api/v1/signup',
  signout: '/api/v1/signout',
  forgotPassword: '/api/v1/forget-password',
  changePassword: '/api/v1/user/change-password',
  adminSignin: '/api/v1/admin/signin',
  verifyEmail: '/api/v1/verify-email',
  resendVerification: '/api/v1/resend-verification',
  oauthSignin: '/api/v1/oauth-signin',
  
  // User endpoints
  profile: '/api/v1/user/profile',
  updateProfile: '/api/v1/user/profile',
  notifyTime: '/api/v1/user/notify-time',
  
  // Course endpoints
  courses: '/api/v1/courses',
  courseDetail: (id: string) => `/api/v1/courses/${id}`,
  
  // Quiz endpoints
  quizzes: '/api/v1/quizzes',
  quizDetail: (id: string) => `/api/v1/quizzes/${id}`,
  submitQuiz: (id: string) => `/api/v1/quizzes/${id}/submit`,
} as const;

// =============================================================================
// 🔧 API UTILITIES
// =============================================================================
export const buildApiUrl = (endpoint: string, baseUrl?: string): string => {
  const base = baseUrl || API_BASE;
  return `${base.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

// =============================================================================
// 💾 LOCAL STORAGE UTILITIES
// =============================================================================
export const storage = {
  // Token management with remember me support
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    // Kiểm tra trong localStorage trước (persistent), sau đó sessionStorage (temporary)
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  },
  setToken: (token: string, remember: boolean = false): void => {
    if (typeof window === 'undefined') return;
    
    if (remember) {
      // Lưu trong localStorage (persistent)
      localStorage.setItem('token', token);
      localStorage.setItem('remember_me', 'true');
      // Xóa khỏi sessionStorage nếu có
      sessionStorage.removeItem('token');
    } else {
      // Lưu trong sessionStorage (temporary)
      sessionStorage.setItem('token', token);
      // Xóa khỏi localStorage nếu có
      localStorage.removeItem('token');
      localStorage.removeItem('remember_me');
    }
  },
  removeToken: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    localStorage.removeItem('remember_me');
  },
  clearSessionToken: (): void => {
    if (typeof window === 'undefined') return;
    // Chỉ xóa session token, giữ lại persistent token nếu có remember me
    sessionStorage.removeItem('token');
  },
  isRemembered: (): boolean => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('remember_me') === 'true';
  },
  
  // Email verification
  getPendingEmail: (): string | null => 
    typeof window !== 'undefined' ? localStorage.getItem('pending_email') : null,
  setPendingEmail: (email: string): void => {
    if (typeof window !== 'undefined') localStorage.setItem('pending_email', email);
  },
  removePendingEmail: (): void => {
    if (typeof window !== 'undefined') localStorage.removeItem('pending_email');
  },
  
  // User preferences
  getTheme: (): string | null => 
    typeof window !== 'undefined' ? localStorage.getItem('theme') : null,
  setTheme: (theme: string): void => {
    if (typeof window !== 'undefined') localStorage.setItem('theme', theme);
  },
  
  // Language preferences
  getLanguage: (): string | null => 
    typeof window !== 'undefined' ? localStorage.getItem('language') : null,
  setLanguage: (language: string): void => {
    if (typeof window !== 'undefined') localStorage.setItem('language', language);
  },
  
  // Generic storage utilities
  get: (key: string): string | null => 
    typeof window !== 'undefined' ? localStorage.getItem(key) : null,
  set: (key: string, value: string): void => {
    if (typeof window !== 'undefined') localStorage.setItem(key, value);
  },
  remove: (key: string): void => {
    if (typeof window !== 'undefined') localStorage.removeItem(key);
  },
  clear: (): void => {
    if (typeof window !== 'undefined') localStorage.clear();
  },
};

// =============================================================================
// 🔒 API REQUEST HEADERS
// =============================================================================
export const getAuthHeaders = (): Record<string, string> => {
  const token = storage.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// =============================================================================
// 🌐 API REQUEST WRAPPER
// =============================================================================
export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export const apiRequest = async <T = unknown>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  try {
    const url = buildApiUrl(endpoint);
    const response = await fetch(url, {
      headers: getAuthHeaders(),
      ...options,
    });

    const data = await response.json();
    
    return {
      data: response.ok ? data : undefined,
      message: data.message,
      error: response.ok ? undefined : data.error || data.message,
      status: response.status,
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
};

// =============================================================================
// 🚀 COMBINED API OBJECT
// =============================================================================
export const api = {
  // Core utilities
  request: apiRequest,
  buildUrl: buildApiUrl,
  getAuthHeaders,
  
  // Endpoints
  endpoints,
  
  // Storage utilities
  storage,
  
  // Base configuration
  baseUrl: API_BASE,
} as const;
