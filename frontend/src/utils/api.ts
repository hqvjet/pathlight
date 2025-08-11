import { API_CONFIG } from '../config/env';
import { cookieStorage } from './cookies';

// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================
export const API_BASE = API_CONFIG.BASE_URL;

export const SERVICE_URLS = {
  AUTH: API_CONFIG.BASE_URL,
  USER: API_CONFIG.BASE_URL,
  COURSE: API_CONFIG.BASE_URL,
  QUIZ: API_CONFIG.BASE_URL,
} as const;

// =============================================================================
// 💾 STORAGE UTILITIES (NOW USING SECURE COOKIES)
// =============================================================================
export const storage = {
  // Token management - now using secure cookies
  getToken: (): string | null => {
    return cookieStorage.getToken();
  },
  
  setToken: (token: string, remember: boolean = false): void => {
    cookieStorage.setToken(token, remember);
  },
  
  removeToken: (): void => {
    cookieStorage.removeToken();
  },
  
  isRemembered: (): boolean => {
    return cookieStorage.isRemembered();
  },
  
  // Email verification - using cookies with expiry
  getPendingEmail: (): string | null => {
    return cookieStorage.getPendingEmail();
  },
  
  setPendingEmail: (email: string): void => {
    cookieStorage.setPendingEmail(email);
  },
  
  removePendingEmail: (): void => {
    cookieStorage.removePendingEmail();
  },
  
  // Generic storage - using cookies
  get: (key: string): string | null => {
    return cookieStorage.get(key);
  },
  
  set: (key: string, value: string): void => {
    cookieStorage.set(key, value);
  },
  
  remove: (key: string): void => {
    cookieStorage.remove(key);
  },
  
  clear: (): void => {
    cookieStorage.clear();
  },
  
  // Additional cookie-specific utilities
  isCookieEnabled: (): boolean => {
    return cookieStorage.isCookieEnabled();
  },
  
  isTokenExpiringSoon: (): boolean => {
    return cookieStorage.isTokenExpiringSoon();
  },
};

// =============================================================================
// 🔒 REQUEST UTILITIES
// =============================================================================
export const getAuthHeaders = (): Record<string, string> => {
  const token = storage.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export const buildApiUrl = (endpoint: string, baseUrl?: string): string => {
  // If targeting Next.js internal API routes, return relative path to current origin
  if (endpoint.startsWith('/api/')) {
    return endpoint;
  }
  const base = baseUrl || API_BASE;
  return `${base.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

export const buildQueryParams = (params: Record<string, unknown>): string => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
};

export const buildUrlWithParams = (endpoint: string, params?: Record<string, unknown>, serviceUrl?: string): string => {
  const baseUrl = serviceUrl ? buildApiUrl(endpoint, serviceUrl) : buildApiUrl(endpoint);
  if (params && Object.keys(params).length > 0) {
    const queryString = buildQueryParams(params);
    return queryString ? `${baseUrl}?${queryString}` : baseUrl;
  }
  return baseUrl;
};

// =============================================================================
// 🚀 API CLIENT
// =============================================================================
export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export const apiRequest = async <T = unknown>(
  endpoint: string, 
  options: RequestInit & { serviceUrl?: string } = {}
): Promise<ApiResponse<T>> => {
  try {
    const { serviceUrl, ...fetchOptions } = options;
    const url = serviceUrl ? buildApiUrl(endpoint, serviceUrl) : buildApiUrl(endpoint);
    
    // Don't automatically add auth headers if custom headers are provided (for FormData uploads)
    const headers = fetchOptions.headers 
      ? fetchOptions.headers 
      : getAuthHeaders();
    
    const response = await fetch(url, {
      headers,
      ...fetchOptions,
    });

    let data;
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
    // Check if the response body contains a status field (for auth service responses)
    if (data && typeof data === 'object' && 'status' in data) {
      return {
        data: data.status === 200 ? data : undefined,
        message: data.message || (data.status === 200 ? 'Success' : 'Request failed'),
        error: data.status === 200 ? undefined : (data.message || `Error ${data.status}`),
        status: data.status,
      };
    }
    
    // Fallback to HTTP status for other services
    return {
      data: response.ok ? data : undefined,
      message: data?.message || (response.ok ? 'Success' : 'Request failed'),
      error: response.ok ? undefined : (data?.error || data?.message || `HTTP ${response.status}`),
      status: response.status,
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 0,
    };
  }
};

// =============================================================================
// 🎯 API METHODS
// =============================================================================
export const api = {
  // Authentication
  auth: {
    signin: (data: unknown) => apiRequest('/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    signup: (data: unknown) => apiRequest('/signup', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    signout: () => apiRequest('/signout', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    verifyEmail: (token: string) => apiRequest(`/verify-email?token=${token}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    resendVerification: (email: string) => apiRequest('/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    forgotPassword: (email: string) => apiRequest('/forget-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    validateResetToken: (token: string) => apiRequest(`/validate-reset-token/${token}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    resetPassword: (token: string, data: unknown) => apiRequest(`/reset-password/${token}`, {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    changePassword: (data: unknown) => apiRequest('/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    oauthSignin: (data: unknown) => apiRequest('/oauth-signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    adminSignin: (data: unknown) => apiRequest('/admin/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
  },
  
  // User management
  user: {
    getProfile: () => apiRequest('/api/user/profile', { 
      method: 'GET',
      serviceUrl: undefined,
    }),
    getMe: () => apiRequest('/api/user/me', { 
      method: 'GET',
      serviceUrl: undefined,
    }),
    getInfo: (id?: string) => apiRequest('/api/user/info', {
      method: 'GET',
      serviceUrl: undefined,
    }),
    getDashboard: () => apiRequest('/api/user/dashboard', {
      method: 'GET',
      serviceUrl: undefined,
    }),
    updateProfile: (data: unknown) => apiRequest('/api/user/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: undefined,
    }),
    updateAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('avatar_file', file);
      return apiRequest('/api/user/avatar', {
        method: 'PUT',
        body: formData,
        headers: {
          ...(storage.getToken() && { Authorization: `Bearer ${storage.getToken()}` }),
        },
        serviceUrl: undefined,
      });
    },
    getAvatar: (userId: string) => apiRequest(`/api/user/avatar?user-id=${encodeURIComponent(userId)}`, {
      method: 'GET',
      serviceUrl: undefined,
    }),
    setNotifyTime: (data: unknown) => apiRequest('/api/user/notify-time', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: undefined,
    }),
    saveActivity: () => apiRequest('/api/user/activity', { 
      method: 'POST',
      serviceUrl: undefined,
    }),
    getAllUsers: () => apiRequest('/api/user', {
      method: 'GET',
      serviceUrl: undefined,
    }),
    getUsersByIds: (userIds: string[]) => apiRequest('/api/user/users-by-ids', {
      method: 'POST',
      body: JSON.stringify(userIds),
      serviceUrl: undefined,
    }),
    
    // Test APIs for development
    test: {
      addExperience: (amount: number) => apiRequest(`/api/user/test/add-experience?exp_amount=${amount}`, {
        method: 'POST',
        serviceUrl: undefined,
      }),
      updateStats: (data: unknown) => apiRequest('/api/user/test/update-stats', {
        method: 'PUT',
        body: JSON.stringify(data),
        serviceUrl: undefined,
      }),
      resetStats: () => apiRequest('/api/user/test/reset-stats', {
        method: 'POST',
        serviceUrl: undefined,
      }),
      simulateActivity: () => apiRequest('/api/user/test/simulate-activity', {
        method: 'GET',
        serviceUrl: undefined,
      }),
      getLevelSystemInfo: () => apiRequest('/api/user/test/level-system-info', {
        method: 'GET',
        serviceUrl: undefined,
      }),
    },

    // Activity data management
    activity: {
      get: () => apiRequest(
        '/api/user/activity', 
        {
          method: 'GET',
          serviceUrl: undefined,
        }
      ),
      save: (data: { date: string; level: number }) => apiRequest('/api/user/activity', {
        method: 'POST',
        body: JSON.stringify(data),
        serviceUrl: undefined,
      }),
      saveBatch: (data: { [key: string]: number }) => apiRequest('/api/user/activity', {
        method: 'POST',
        body: JSON.stringify({ activityData: data }),
        serviceUrl: undefined,
      }),
      clear: () => apiRequest('/api/user/activity', {
        method: 'DELETE',
        serviceUrl: undefined,
      }),
    },
  },
  
  // Course management
  course: {
    getAll: (params?: Record<string, unknown>) => apiRequest(
      buildUrlWithParams('/courses', params),
      { 
        method: 'GET',
        serviceUrl: SERVICE_URLS.COURSE,
      }
    ),
    getById: (id: string) => apiRequest(`/courses/${id}`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    create: (data: unknown) => apiRequest('/courses', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    update: (id: string, data: unknown) => apiRequest(`/courses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    delete: (id: string) => apiRequest(`/courses/${id}`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    enroll: (id: string) => apiRequest(`/courses/${id}/enroll`, { 
      method: 'POST',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    unenroll: (id: string) => apiRequest(`/courses/${id}/unenroll`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    getEnrollments: () => apiRequest('/courses/enrollments', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
  },
  
  // Quiz management
  quiz: {
    getAll: (params?: Record<string, unknown>) => apiRequest(
      buildUrlWithParams('/quizzes', params),
      { 
        method: 'GET',
        serviceUrl: SERVICE_URLS.QUIZ,
      }
    ),
    getById: (id: string) => apiRequest(`/quizzes/${id}`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    create: (data: unknown) => apiRequest('/quizzes', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    update: (id: string, data: unknown) => apiRequest(`/quizzes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    delete: (id: string) => apiRequest(`/quizzes/${id}`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    submit: (id: string, answers: unknown) => apiRequest(`/quizzes/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getResult: (id: string) => apiRequest(`/quizzes/${id}/result`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getHistory: () => apiRequest('/quizzes/history', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getUserQuizzes: () => apiRequest('/quizzes', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
  },
};

// =============================================================================
// 🔄 BACKWARD COMPATIBILITY - DEPRECATED
// =============================================================================
// Keep old exports for backward compatibility
export const endpoints = {
  // Auth endpoints (will automatically get /auth prefix)
  signin: '/signin',
  signup: '/signup',
  signout: '/signout',
  verifyEmail: '/verify-email',
  resendVerification: '/resend-verification',
  forgotPassword: '/forget-password',
  validateResetToken: (token: string) => `/validate-reset-token/${token}`,
  resetPassword: (token: string) => `/reset-password/${token}`,
  changePassword: '/change-password',
  oauthSignin: '/oauth-signin',
  adminSignin: '/admin/signin',
  
  // User endpoints via Next.js API proxies
  profile: '/api/user/profile',
  me: '/api/user/me',
  info: '/api/user/info',
  changeInfo: '/api/user/profile',
  avatar: '/api/user/avatar',
  notifyTime: '/api/user/notify-time',
  dashboard: '/api/user/dashboard',
  activity: '/api/user/activity',
  allUsers: '/api/user',
  
  // Course endpoints (no prefix needed)
  courses: '/courses',
  courseDetail: (id: string) => `/courses/${id}`,
  
  // Quiz endpoints (no prefix needed)
  quizzes: '/quizzes',
  quizDetail: (id: string) => `/quizzes/${id}`,
  submitQuiz: (id: string) => `/quizzes/${id}/submit`,
} as const;
