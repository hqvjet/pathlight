import { API_CONFIG } from '../config/env';

// =============================================================================
// 🌐 API CONFIGURATION
// =============================================================================
export const API_BASE = API_CONFIG.BASE_URL;

export const SERVICE_URLS = {
  AUTH: API_CONFIG.AUTH_SERVICE_URL,
  USER: API_CONFIG.USER_SERVICE_URL,
  COURSE: API_CONFIG.COURSE_SERVICE_URL,
  QUIZ: API_CONFIG.QUIZ_SERVICE_URL,
} as const;

// =============================================================================
// 💾 STORAGE UTILITIES
// =============================================================================
export const storage = {
  // Token management
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  },
  
  setToken: (token: string, remember: boolean = false): void => {
    if (typeof window === 'undefined') return;
    
    if (remember) {
      localStorage.setItem('token', token);
      localStorage.setItem('remember_me', 'true');
      sessionStorage.removeItem('token');
    } else {
      sessionStorage.setItem('token', token);
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
  
  // Generic storage
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
  const base = baseUrl || API_BASE;
  return `${base.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

export const buildQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
};

export const buildUrlWithParams = (endpoint: string, params?: Record<string, any>, serviceUrl?: string): string => {
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
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export const apiRequest = async <T = any>(
  endpoint: string, 
  options: RequestInit & { serviceUrl?: string } = {}
): Promise<ApiResponse<T>> => {
  try {
    const { serviceUrl, ...fetchOptions } = options;
    const url = serviceUrl ? buildApiUrl(endpoint, serviceUrl) : buildApiUrl(endpoint);
    
    const response = await fetch(url, {
      headers: getAuthHeaders(),
      ...fetchOptions,
    });

    let data;
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
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
    signin: (data: any) => apiRequest('/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    signup: (data: any) => apiRequest('/signup', {
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
    resetPassword: (token: string, data: any) => apiRequest(`/reset-password/${token}`, {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    changePassword: (data: any) => apiRequest('/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    oauthSignin: (data: any) => apiRequest('/oauth-signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
    adminSignin: (data: any) => apiRequest('/admin/signin', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.AUTH,
    }),
  },
  
  // User management
  user: {
    getProfile: () => apiRequest('/profile', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getMe: () => apiRequest('/me', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getInfo: (id?: string) => apiRequest(id ? `/info?id=${id}` : '/info', {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    updateProfile: (data: any) => apiRequest('/change-info', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.USER,
    }),
    updateAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('avatar_file', file);
      return apiRequest('/avatar', {
        method: 'PUT',
        body: formData,
        headers: {
          ...(storage.getToken() && { Authorization: `Bearer ${storage.getToken()}` }),
        },
        serviceUrl: SERVICE_URLS.USER,
      });
    },
    getAvatar: (avatarId: string) => apiRequest(`/avatar/?avatar_id=${avatarId}`, {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getDashboard: () => apiRequest('/dashboard', { 
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
    setNotifyTime: (data: any) => apiRequest('/notify-time', {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.USER,
    }),
    saveActivity: () => apiRequest('/activity', { 
      method: 'POST',
      serviceUrl: SERVICE_URLS.USER,
    }),
    getAllUsers: () => apiRequest('/all', {
      method: 'GET',
      serviceUrl: SERVICE_URLS.USER,
    }),
  },
  
  // Course management
  course: {
    getAll: (params?: Record<string, any>) => apiRequest(
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
    create: (data: any) => apiRequest('/courses', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.COURSE,
    }),
    update: (id: string, data: any) => apiRequest(`/courses/${id}`, {
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
    getAll: (params?: Record<string, any>) => apiRequest(
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
    create: (data: any) => apiRequest('/quizzes', {
      method: 'POST',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    update: (id: string, data: any) => apiRequest(`/quizzes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    delete: (id: string) => apiRequest(`/quizzes/${id}`, { 
      method: 'DELETE',
      serviceUrl: SERVICE_URLS.QUIZ,
    }),
    submit: (id: string, answers: any) => apiRequest(`/quizzes/${id}/submit`, {
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
  // Auth endpoints
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
  
  // User endpoints
  profile: '/profile',
  me: '/me',
  info: '/info',
  changeInfo: '/change-info',
  avatar: '/avatar',
  notifyTime: '/notify-time',
  dashboard: '/dashboard',
  activity: '/activity',
  allUsers: '/all',
  
  // Course endpoints
  courses: '/courses',
  courseDetail: (id: string) => `/courses/${id}`,
  
  // Quiz endpoints
  quizzes: '/quizzes',
  quizDetail: (id: string) => `/quizzes/${id}`,
  submitQuiz: (id: string) => `/quizzes/${id}/submit`,
} as const;
