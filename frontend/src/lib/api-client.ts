/**
 * =============================================================================
 * 🌐 PATHLIGHT FRONTEND - ADVANCED API CLIENT
 * =============================================================================
 * Enhanced API client with interceptors, error handling, and retry logic
 */

import { API_CONFIG } from '../config/env';
import { API_CONSTANTS, ERROR_CONSTANTS, STORAGE_KEYS } from '../constants';

// =============================================================================
// 🔧 TYPES & INTERFACES
// =============================================================================

export interface ApiRequestConfig extends RequestInit {
  baseURL?: string;
  timeout?: number;
  retry?: {
    attempts: number;
    delay: number;
  };
  skipAuth?: boolean;
}

export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
  success: boolean;
}

export interface ApiError extends Error {
  message: string;
  status: number;
  code?: string;
  details?: unknown;
}

export class ApiErrorClass extends Error implements ApiError {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// =============================================================================
// 🔐 TOKEN MANAGEMENT
// =============================================================================

class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<string> | null = null;

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
  }

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEYS.TOKEN, token);
  }

  removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  }

  setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
  }

  async refreshToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_CONFIG.BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      this.removeToken();
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    const newToken = data.access_token;
    
    this.setToken(newToken);
    
    if (data.refresh_token) {
      this.setRefreshToken(data.refresh_token);
    }

    return newToken;
  }
}

// =============================================================================
// 🗺️ SERVICE ROUTER
// =============================================================================

class ServiceRouter {
  private static instance: ServiceRouter;
  
  static getInstance(): ServiceRouter {
    if (!ServiceRouter.instance) {
      ServiceRouter.instance = new ServiceRouter();
    }
    return ServiceRouter.instance;
  }

  /**
   * Route endpoints to appropriate API paths
   */
  getServiceUrl(): string {
    return API_CONFIG.BASE_URL;
  }

  /**
   * Add appropriate prefix to endpoints based on their type
   */
  buildEndpointWithPrefix(endpoint: string): string {
    const cleanEndpoint = endpoint.toLowerCase();
    
    // User endpoints should go through /api/users prefix
    if (cleanEndpoint.startsWith('/api/users/')) {
      return endpoint; // Already has the correct prefix
    }
    
    // Auth endpoints should have /auth prefix
    if (cleanEndpoint.includes('/signin') || 
        cleanEndpoint.includes('/signup') || 
        cleanEndpoint.includes('/login') || 
        cleanEndpoint.includes('/register') || 
        cleanEndpoint.includes('/signout') ||
        cleanEndpoint.includes('/refresh') ||
        cleanEndpoint.includes('/verify') ||
        cleanEndpoint.includes('/forgot-password') ||
        cleanEndpoint.includes('/reset-password') ||
        cleanEndpoint.includes('/change-password') ||
        cleanEndpoint.includes('/oauth') ||
        cleanEndpoint.includes('/resend-verification') ||
        cleanEndpoint.includes('/forget-password') ||
        cleanEndpoint.includes('/validate-reset-token') ||
        cleanEndpoint.startsWith('/auth/')) {
      
      // If endpoint already starts with /auth, don't add it again
      if (endpoint.startsWith('/auth/')) {
        return endpoint;
      }
      
      // Add /auth prefix, ensuring no double slashes
      const cleanPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      return `/auth${cleanPath}`;
    }
    
    // For non-auth endpoints, return as is
    return endpoint;
  }
}

// =============================================================================
// 🌐 API CLIENT CLASS
// =============================================================================

export class ApiClient {
  private baseURL: string;
  private defaultTimeout: number;
  private tokenManager: TokenManager;
  private serviceRouter: ServiceRouter;

  constructor(baseURL: string = API_CONFIG.BASE_URL) {
    this.baseURL = baseURL;
    this.defaultTimeout = API_CONSTANTS.TIMEOUT;
    this.tokenManager = TokenManager.getInstance();
    this.serviceRouter = ServiceRouter.getInstance();
  }

  // =============================================================================
  // 🔧 PRIVATE METHODS
  // =============================================================================

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private buildUrl(endpoint: string, baseURL?: string): string {
    // Use provided baseURL or get service URL
    const base = baseURL || this.serviceRouter.getServiceUrl() || this.baseURL;
    const cleanBase = base.replace(/\/$/, '');
    
    // Build endpoint with appropriate prefix
    const endpointWithPrefix = this.serviceRouter.buildEndpointWithPrefix(endpoint);
    const cleanEndpoint = endpointWithPrefix.startsWith('/') ? endpointWithPrefix : `/${endpointWithPrefix}`;
    
    return `${cleanBase}${cleanEndpoint}`;
  }

  private async buildHeaders(config: ApiRequestConfig): Promise<HeadersInit> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    // Add authentication header if not skipped
    if (!config.skipAuth) {
      const token = this.tokenManager.getToken();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
    }

    // Merge with provided headers
    if (config.headers) {
      const configHeaders = config.headers as Record<string, string>;
      Object.assign(headers, configHeaders);
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    let data: unknown;
    
    try {
      const text = await response.text();
      data = text ? JSON.parse(text) : null;
    } catch {
      data = null;
    }

    const apiResponse: ApiResponse<T> = {
      data: response.ok ? (data as T) : undefined,
      message: (data as Record<string, unknown>)?.message as string || (data as Record<string, unknown>)?.detail as string,
      error: response.ok ? undefined : ((data as Record<string, unknown>)?.error as string || (data as Record<string, unknown>)?.detail as string || response.statusText),
      status: response.status,
      success: response.ok,
    };

    if (!response.ok) {
      throw this.createApiError(apiResponse);
    }

    return apiResponse;
  }

  private createApiError(response: ApiResponse): ApiErrorClass {
    let message = response.error || ERROR_CONSTANTS.MESSAGES.SERVER_ERROR;
    let code: string | undefined;

    // Map status codes to error codes
    switch (response.status) {
      case API_CONSTANTS.STATUS_CODES.UNAUTHORIZED:
        code = ERROR_CONSTANTS.CODES.AUTHENTICATION_ERROR;
        message = ERROR_CONSTANTS.MESSAGES.UNAUTHORIZED;
        break;
      case API_CONSTANTS.STATUS_CODES.FORBIDDEN:
        code = ERROR_CONSTANTS.CODES.AUTHORIZATION_ERROR;
        message = ERROR_CONSTANTS.MESSAGES.FORBIDDEN;
        break;
      case API_CONSTANTS.STATUS_CODES.NOT_FOUND:
        code = ERROR_CONSTANTS.CODES.NOT_FOUND_ERROR;
        message = ERROR_CONSTANTS.MESSAGES.NOT_FOUND;
        break;
      case API_CONSTANTS.STATUS_CODES.BAD_REQUEST:
        code = ERROR_CONSTANTS.CODES.VALIDATION_ERROR;
        message = response.error || ERROR_CONSTANTS.MESSAGES.VALIDATION_ERROR;
        break;
      default:
        code = ERROR_CONSTANTS.CODES.SERVER_ERROR;
        break;
    }

    return new ApiErrorClass(message, response.status, code);
  }

  private async executeRequest<T>(
    url: string,
    config: ApiRequestConfig
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeout = config.timeout || this.defaultTimeout;

    // Set up timeout
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const headers = await this.buildHeaders(config);
      
      const response = await fetch(url, {
        ...config,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle 401 errors with token refresh
      if (response.status === API_CONSTANTS.STATUS_CODES.UNAUTHORIZED && !config.skipAuth) {
        try {
          await this.tokenManager.refreshToken();
          
          // Retry the request with new token
          const newHeaders = await this.buildHeaders(config);
          const retryResponse = await fetch(url, {
            ...config,
            headers: newHeaders,
            signal: controller.signal,
          });

          return this.handleResponse<T>(retryResponse);
        } catch (refreshError) {
          // Token refresh failed, remove tokens and redirect to login
          this.tokenManager.removeToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/signin';
          }
          throw refreshError;
        }
      }

      return this.handleResponse<T>(response);
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiErrorClass) {
        throw error;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new Error(ERROR_CONSTANTS.MESSAGES.TIMEOUT_ERROR);
      }

      throw new Error(ERROR_CONSTANTS.MESSAGES.NETWORK_ERROR);
    }
  }

  // =============================================================================
  // 🔄 RETRY LOGIC
  // =============================================================================

  private async executeWithRetry<T>(
    url: string,
    config: ApiRequestConfig
  ): Promise<ApiResponse<T>> {
    const retry = config.retry || {
      attempts: API_CONSTANTS.RETRY_ATTEMPTS,
      delay: API_CONSTANTS.RETRY_DELAY,
    };

    let lastError: Error | null = null;

    for (let attempt = 0; attempt < retry.attempts; attempt++) {
      try {
        return await this.executeRequest<T>(url, config);
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on certain errors
        if (error instanceof ApiErrorClass) {
          const noRetryStatuses = [
            400, // BAD_REQUEST
            401, // UNAUTHORIZED
            403, // FORBIDDEN
            404, // NOT_FOUND
          ];
          
          if (noRetryStatuses.includes(error.status)) {
            throw error;
          }
        }

        // Wait before retry (except for last attempt)
        if (attempt < retry.attempts - 1) {
          await this.sleep(retry.delay * (attempt + 1));
        }
      }
    }

    throw lastError;
  }

  // =============================================================================
  // 🌐 PUBLIC HTTP METHODS
  // =============================================================================

  async get<T>(endpoint: string, config: ApiRequestConfig = {}): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    return this.executeWithRetry<T>(url, { ...config, method: 'GET' });
  }

  async post<T>(
    endpoint: string,
    data?: unknown,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    return this.executeWithRetry<T>(url, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(
    endpoint: string,
    data?: unknown,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    return this.executeWithRetry<T>(url, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(
    endpoint: string,
    data?: unknown,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    return this.executeWithRetry<T>(url, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string, config: ApiRequestConfig = {}): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    return this.executeWithRetry<T>(url, { ...config, method: 'DELETE' });
  }

  // =============================================================================
  // 📎 FILE UPLOAD METHODS
  // =============================================================================

  async uploadFile<T>(
    endpoint: string,
    file: File,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    const formData = new FormData();
    formData.append('file', file);

    const headers = await this.buildHeaders({ ...config, skipAuth: config.skipAuth });
    delete (headers as Record<string, string>)['Content-Type']; // Let browser set content-type for FormData

    return this.executeWithRetry<T>(url, {
      ...config,
      method: 'POST',
      body: formData,
      headers,
    });
  }

  async uploadMultipleFiles<T>(
    endpoint: string,
    files: File[],
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, config.baseURL);
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });

    const headers = await this.buildHeaders({ ...config, skipAuth: config.skipAuth });
    delete (headers as Record<string, string>)['Content-Type'];

    return this.executeWithRetry<T>(url, {
      ...config,
      method: 'POST',
      body: formData,
      headers,
    });
  }
}

// =============================================================================
// 🏭 SINGLETON INSTANCE
// =============================================================================

export const apiClient = new ApiClient();

// =============================================================================
// 🔗 CONVENIENCE METHODS
// =============================================================================

export const api = {
  // Generic HTTP methods
  get: <T>(endpoint: string, config?: ApiRequestConfig) => 
    apiClient.get<T>(endpoint, config),
  
  post: <T>(endpoint: string, data?: unknown, config?: ApiRequestConfig) => 
    apiClient.post<T>(endpoint, data, config),
  
  put: <T>(endpoint: string, data?: unknown, config?: ApiRequestConfig) => 
    apiClient.put<T>(endpoint, data, config),
  
  patch: <T>(endpoint: string, data?: unknown, config?: ApiRequestConfig) => 
    apiClient.patch<T>(endpoint, data, config),
  
  delete: <T>(endpoint: string, config?: ApiRequestConfig) => 
    apiClient.delete<T>(endpoint, config),

  uploadFile: <T>(endpoint: string, file: File, config?: ApiRequestConfig) => 
    apiClient.uploadFile<T>(endpoint, file, config),

  uploadFiles: <T>(endpoint: string, files: File[], config?: ApiRequestConfig) => 
    apiClient.uploadMultipleFiles<T>(endpoint, files, config),

  // Structured API methods for better developer experience
  auth: {
    signin: (data: unknown) => apiClient.post('/signin', data),
    signup: (data: unknown) => apiClient.post('/signup', data),
    signout: () => apiClient.post('/signout'),
    verifyEmail: (token: string) => apiClient.get(`/verify-email?token=${token}`),
    resendVerification: (email: string) => apiClient.post('/resend-verification', { email }),
    forgotPassword: (email: string) => apiClient.post('/forget-password', { email }),
    validateResetToken: (token: string) => apiClient.get(`/validate-reset-token/${token}`),
    resetPassword: (token: string, data: unknown) => apiClient.post(`/reset-password/${token}`, data),
    changePassword: (data: unknown) => apiClient.post('/change-password', data),
    oauthSignin: (data: unknown) => apiClient.post('/oauth-signin', data),
    refresh: (refreshToken: string) => apiClient.post('/refresh', { refresh_token: refreshToken }),
  },

  user: {
    getProfile: () => apiClient.get('/api/users/profile'),
    getMe: () => apiClient.get('/api/users/me'),
    getDashboard: () => apiClient.get('/api/users/dashboard'),
    updateProfile: (data: unknown) => apiClient.put('/api/users/profile', data),
    updateAvatar: (file: File) => apiClient.uploadFile('/api/users/avatar', file),
    getAvatar: (userId: string) => apiClient.get(`/api/users/avatar?user_id=${userId}`),
    setNotifyTime: (data: unknown) => apiClient.put('/api/users/notify-time', data),
    saveActivity: () => apiClient.post('/api/users/activity'),
    getAllUsers: () => apiClient.get('/api/users'),
    getActivity: (year?: number) => apiClient.get(year ? `/api/users/activity?year=${year}` : '/api/users/activity'),
    getUsersByIds: (userIds: string[]) => apiClient.post('/api/users/users-by-ids', userIds),
  },

  course: {
    getAll: (params?: Record<string, unknown>) => {
      const queryString = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/courses${queryString}`);
    },
    getById: (id: string) => apiClient.get(`/courses/${id}`),
    create: (data: unknown) => apiClient.post('/courses', data),
    update: (id: string, data: unknown) => apiClient.put(`/courses/${id}`, data),
    delete: (id: string) => apiClient.delete(`/courses/${id}`),
    enroll: (id: string) => apiClient.post(`/courses/${id}/enroll`),
    unenroll: (id: string) => apiClient.delete(`/courses/${id}/unenroll`),
    getEnrollments: () => apiClient.get('/courses/enrollments'),
  },

  quiz: {
    getAll: (params?: Record<string, unknown>) => {
      const queryString = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/quizzes${queryString}`);
    },
    getById: (id: string) => apiClient.get(`/quizzes/${id}`),
    create: (data: unknown) => apiClient.post('/quizzes', data),
    update: (id: string, data: unknown) => apiClient.put(`/quizzes/${id}`, data),
    delete: (id: string) => apiClient.delete(`/quizzes/${id}`),
    submit: (id: string, answers: unknown) => apiClient.post(`/quizzes/${id}/submit`, { answers }),
    getResult: (id: string) => apiClient.get(`/quizzes/${id}/result`),
    getHistory: () => apiClient.get('/quizzes/history'),
  },
};

export default api;
