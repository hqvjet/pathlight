import { API_CONFIG } from '../config/env';
import { cookieStorage } from './cookies';

// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================
export const API_BASE = API_CONFIG.BASE_URL;

export const SERVICE_URLS = {
  AUTH: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || API_CONFIG.BASE_URL,
  USER: process.env.NEXT_PUBLIC_USER_SERVICE_URL || API_CONFIG.BASE_URL,
  COURSE: process.env.NEXT_PUBLIC_COURSE_SERVICE_URL || API_CONFIG.BASE_URL,
  QUIZ: process.env.NEXT_PUBLIC_QUIZ_SERVICE_URL || API_CONFIG.BASE_URL,
  // AUTH: 'http://localhost:8001',
  // USER: 'http://localhost:8002',
  // COURSE: 'http://localhost:8003',
  // QUIZ: 'http://localhost:8004',
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
  // If no baseUrl is provided and targeting Next.js internal API routes, return relative path to current origin
  if (endpoint.startsWith('/api/') && !baseUrl) {
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
    signin: (data: unknown) => apiRequest('/auth/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    signup: (data: unknown) => apiRequest('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    signout: () => apiRequest('/auth/signout', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    verifyEmail: (token: string) => apiRequest(`/auth/verify-email?token=${token}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    resendVerification: (email: string) => apiRequest('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    forgotPassword: (email: string) => apiRequest('/auth/forget-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    validateResetToken: (token: string) => apiRequest(`/auth/validate-reset-token/${token}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    resetPassword: (token: string, data: unknown) => apiRequest(`/auth/reset-password/${token}`, {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    changePassword: (data: unknown) => apiRequest('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    oauthSignin: (data: unknown) => apiRequest('/auth/oauth-signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    adminSignin: (data: unknown) => apiRequest('/auth/admin/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
  },
  
  // User management
  user: {
    getProfile: () => apiRequest('/api/users/profile', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getMe: () => apiRequest('/api/users/me', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getInfo: (id?: string) => apiRequest(id ? `/api/users/info?id=${id}` : '/api/users/info', {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getDashboard: () => apiRequest('/api/users/dashboard', {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    updateProfile: (data: unknown) => apiRequest('/api/users/change-info', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.USER,
    }),
    updateAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('avatar_file', file);
      return apiRequest('/api/users/avatar', {
        method: 'PUT',
        body: formData,
        headers: {
          // Let browser set Content-Type for FormData
          ...(storage.getToken() && { Authorization: `Bearer ${storage.getToken()}` }),
        },
        serviceUrl: SERVICE_URLS.USER,
      });
    },
    getAvatar: (userId: string) => apiRequest(`/api/users/avatar?user_id=${userId}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    setNotifyTime: (data: unknown) => apiRequest('/api/users/notify-time', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.USER,
    }),
    saveActivity: () => apiRequest('/api/users/activity', { 
      method: 'POST',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getAllUsers: () => apiRequest('/api/users', {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getUsersByIds: (userIds: string[]) => apiRequest('/api/users/users-by-ids', {
      method: 'POST',
      body: JSON.stringify(userIds),
      serviceUrl: SERVICE_URLS.USER,
    }),
    
    // Test APIs for development
    test: {
      addExperience: (amount: number) => apiRequest(`/api/users/test/add-experience?exp_amount=${amount}`, {
        method: 'POST',
        serviceUrl: SERVICE_URLS.USER,
      }),
      updateStats: (data: unknown) => apiRequest('/api/users/test/update-stats', {
        method: 'PUT',
        body: JSON.stringify(data),
        serviceUrl: SERVICE_URLS.USER,
      }),
      resetStats: () => apiRequest('/api/users/test/reset-stats', {
        method: 'POST',
        serviceUrl: SERVICE_URLS.USER,
      }),
      simulateActivity: () => apiRequest('/api/users/test/simulate-activity', {
        method: 'GET',
        serviceUrl: SERVICE_URLS.USER,
      }),
      getLevelSystemInfo: () => apiRequest('/api/users/test/level-system-info', {
        method: 'GET',
        serviceUrl: SERVICE_URLS.USER,
      }),
    },

    // Activity data management
    activity: {
      get: (year?: number) => apiRequest(
        year ? `/api/users/activity?year=${year}` : '/api/users/activity', 
        {
          method: 'GET',
          serviceUrl: SERVICE_URLS.USER,
        }
      ),
      save: (data: { date: string; level: number }) => apiRequest('/api/users/activity', {
        method: 'POST',
        body: JSON.stringify(data),
        serviceUrl: SERVICE_URLS.USER,
      }),
      saveBatch: (data: { [key: string]: number }) => apiRequest('/api/users/activity', {
        method: 'POST',
        body: JSON.stringify({ activityData: data }),
        serviceUrl: SERVICE_URLS.USER,
      }),
      clear: () => apiRequest('/api/users/activity', {
        method: 'DELETE',
        serviceUrl: SERVICE_URLS.USER,
      }),
    },
  },
  
  // Course management
  course: {
    getAll: (params?: Record<string, unknown>) => apiRequest(
      buildUrlWithParams('/course', params),
      { 
        method: 'GET',
        serviceUrl: SERVICE_URLS.COURSE,
      }
    ),
    getById: (id: string) => apiRequest(`/course/${id}`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    create: (data: unknown) => apiRequest('/course', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    update: (id: string, data: unknown) => apiRequest(`/course/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    delete: (id: string) => apiRequest(`/course/${id}`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    enroll: (id: string) => apiRequest(`/course/${id}/enroll`, { 
      method: 'POST',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    unenroll: (id: string) => apiRequest(`/course/${id}/unenroll`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    getEnrollments: () => apiRequest('/course/enrollments', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.COURSE,
    }),
  },
  
  // Quiz management
  quiz: {
    getAll: (params?: Record<string, unknown>) => apiRequest(
      buildUrlWithParams('/quiz', params),
      { 
        method: 'GET',
        serviceUrl: SERVICE_URLS.QUIZ,
      }
    ),
    getById: (id: string) => apiRequest(`/quiz/${id}`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    create: (data: unknown) => apiRequest('/quiz', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    update: (id: string, data: unknown) => apiRequest(`/quiz/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    delete: (id: string) => apiRequest(`/quiz/${id}`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    submit: (id: string, answers: unknown) => apiRequest(`/quiz/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getResult: (id: string) => apiRequest(`/quiz/${id}/result`, { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getHistory: () => apiRequest('/quiz/history', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    getUserquiz: () => apiRequest('/quiz', { 
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
  profile: '/api/users/profile',
  me: '/api/users/me',
  info: '/api/users/info',
  changeInfo: '/api/users/profile',
  avatar: '/api/users/avatar',
  notifyTime: '/api/users/notify-time',
  dashboard: '/api/users/dashboard',
  activity: '/api/users/activity',
  allUsers: '/api/users',
  
  // Course endpoints (no prefix needed)
  course: '/course',
  courseDetail: (id: string) => `/course/${id}`,
  
  // Quiz endpoints (no prefix needed)
  quiz: '/quiz',
  quizDetail: (id: string) => `/quiz/${id}`,
  submitQuiz: (id: string) => `/quiz/${id}/submit`,
} as const;
