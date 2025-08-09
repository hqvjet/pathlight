/**
 * Core HTTP client, token management, routing utilities
 * Extracted from legacy api-client.ts for modular structure
 */
import { API_CONFIG } from '../../config/env';
import { API_CONSTANTS, ERROR_CONSTANTS, STORAGE_KEYS } from '../../constants';

// =============================
// Types
// =============================
export interface ApiRequestConfig extends RequestInit {
  baseURL?: string;
  timeout?: number;
  retry?: { attempts: number; delay: number };
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

// =============================
// Token Manager
// =============================
class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<string> | null = null;
  static getInstance() {
    if (!TokenManager.instance) TokenManager.instance = new TokenManager();
    return TokenManager.instance;
  }
  getToken() { return typeof window === 'undefined' ? null : localStorage.getItem(STORAGE_KEYS.TOKEN); }
  setToken(token: string) { if (typeof window !== 'undefined') localStorage.setItem(STORAGE_KEYS.TOKEN, token); }
  removeToken() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }
  getRefreshToken() { return typeof window === 'undefined' ? null : localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN); }
  setRefreshToken(token: string) { if (typeof window !== 'undefined') localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token); }
  async refreshToken(): Promise<string> {
    if (this.refreshPromise) return this.refreshPromise;
    this.refreshPromise = this.performTokenRefresh();
    try { return await this.refreshPromise; } finally { this.refreshPromise = null; }
  }
  private async performTokenRefresh(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token available');
    const response = await fetch(`${API_CONFIG.BASE_URL}/auth/refresh`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) });
    if (!response.ok) { this.removeToken(); throw new Error('Token refresh failed'); }
    const data = await response.json();
    const newToken = data.access_token; this.setToken(newToken); if (data.refresh_token) this.setRefreshToken(data.refresh_token); return newToken;
  }
}

// =============================
// Service Router
// =============================
class ServiceRouter {
  private static instance: ServiceRouter;
  static getInstance() { if (!ServiceRouter.instance) ServiceRouter.instance = new ServiceRouter(); return ServiceRouter.instance; }
  getServiceUrl(): string { return API_CONFIG.BASE_URL; }
  buildEndpointWithPrefix(endpoint: string): string {
    const cleanEndpoint = endpoint.toLowerCase();
    if (cleanEndpoint.startsWith('/api/users/')) return endpoint;
    if (cleanEndpoint.includes('/signin') || cleanEndpoint.includes('/signup') || cleanEndpoint.includes('/login') || cleanEndpoint.includes('/register') || cleanEndpoint.includes('/signout') || cleanEndpoint.includes('/refresh') || cleanEndpoint.includes('/verify') || cleanEndpoint.includes('/forgot-password') || cleanEndpoint.includes('/reset-password') || cleanEndpoint.includes('/change-password') || cleanEndpoint.includes('/oauth') || cleanEndpoint.includes('/resend-verification') || cleanEndpoint.includes('/forget-password') || cleanEndpoint.includes('/validate-reset-token') || cleanEndpoint.startsWith('/auth/')) {
      if (endpoint.startsWith('/auth/')) return endpoint;
      const cleanPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      return `/auth${cleanPath}`;
    }
    return endpoint;
  }
}

// =============================
// ApiClient
// =============================
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
  private sleep(ms: number) { return new Promise(res => setTimeout(res, ms)); }
  private buildUrl(endpoint: string, baseURL?: string) {
    const base = (baseURL || this.serviceRouter.getServiceUrl() || this.baseURL).replace(/\/$/, '');
    const endpointWithPrefix = this.serviceRouter.buildEndpointWithPrefix(endpoint);
    const cleanEndpoint = endpointWithPrefix.startsWith('/') ? endpointWithPrefix : `/${endpointWithPrefix}`;
    return `${base}${cleanEndpoint}`;
  }
  private async buildHeaders(config: ApiRequestConfig): Promise<HeadersInit> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
    if (!config.skipAuth) { const token = this.tokenManager.getToken(); if (token) headers.Authorization = `Bearer ${token}`; }
    if (config.headers) Object.assign(headers, config.headers as Record<string, string>);
    return headers;
  }
  private createApiError(response: ApiResponse): ApiErrorClass {
    let message = response.error || ERROR_CONSTANTS.MESSAGES.SERVER_ERROR; let code: string | undefined;
    switch (response.status) {
      case API_CONSTANTS.STATUS_CODES.UNAUTHORIZED: code = ERROR_CONSTANTS.CODES.AUTHENTICATION_ERROR; message = ERROR_CONSTANTS.MESSAGES.UNAUTHORIZED; break;
      case API_CONSTANTS.STATUS_CODES.FORBIDDEN: code = ERROR_CONSTANTS.CODES.AUTHORIZATION_ERROR; message = ERROR_CONSTANTS.MESSAGES.FORBIDDEN; break;
      case API_CONSTANTS.STATUS_CODES.NOT_FOUND: code = ERROR_CONSTANTS.CODES.NOT_FOUND_ERROR; message = ERROR_CONSTANTS.MESSAGES.NOT_FOUND; break;
      case API_CONSTANTS.STATUS_CODES.BAD_REQUEST: code = ERROR_CONSTANTS.CODES.VALIDATION_ERROR; message = response.error || ERROR_CONSTANTS.MESSAGES.VALIDATION_ERROR; break;
      default: code = ERROR_CONSTANTS.CODES.SERVER_ERROR; break; }
    return new ApiErrorClass(message, response.status, code);
  }
  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    let data: unknown; try { const text = await response.text(); data = text ? JSON.parse(text) : null; } catch { data = null; }
    const body = data as { message?: string; detail?: string; error?: string } | null;
    const apiResponse: ApiResponse<T> = { data: response.ok ? (data as T) : undefined, message: body?.message || body?.detail, error: response.ok ? undefined : (body?.error || body?.detail || response.statusText), status: response.status, success: response.ok };
    if (!response.ok) throw this.createApiError(apiResponse);
    return apiResponse;
  }
  private async executeRequest<T>(url: string, config: ApiRequestConfig): Promise<ApiResponse<T>> {
    const controller = new AbortController(); const timeout = config.timeout || this.defaultTimeout; const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const headers = await this.buildHeaders(config);
      const response = await fetch(url, { ...config, headers, signal: controller.signal });
      clearTimeout(timeoutId);
      if (response.status === API_CONSTANTS.STATUS_CODES.UNAUTHORIZED && !config.skipAuth) {
        try {
          await this.tokenManager.refreshToken();
          const newHeaders = await this.buildHeaders(config);
            const retryResponse = await fetch(url, { ...config, headers: newHeaders, signal: controller.signal });
            return this.handleResponse<T>(retryResponse);
        } catch (refreshError) {
          this.tokenManager.removeToken(); if (typeof window !== 'undefined') window.location.href = '/auth/signin'; throw refreshError;
        }
      }
      return this.handleResponse<T>(response);
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof ApiErrorClass) throw error;
      if (error instanceof DOMException && error.name === 'AbortError') throw new Error(ERROR_CONSTANTS.MESSAGES.TIMEOUT_ERROR);
      throw new Error(ERROR_CONSTANTS.MESSAGES.NETWORK_ERROR);
    }
   }
  private async executeWithRetry<T>(url: string, config: ApiRequestConfig): Promise<ApiResponse<T>> {
    const retry = config.retry || { attempts: API_CONSTANTS.RETRY_ATTEMPTS, delay: API_CONSTANTS.RETRY_DELAY };
     let lastError: Error | null = null;
    for (let attempt = 0; attempt < retry.attempts; attempt++) {
      try { return await this.executeRequest<T>(url, config); } catch (error) {
        lastError = error as Error;
        if (error instanceof ApiErrorClass) {
          const noRetryStatuses = [400,401,403,404]; if (noRetryStatuses.includes(error.status)) throw error; }
         if (attempt < retry.attempts - 1) await this.sleep(retry.delay * (attempt + 1));
       }
     }
     throw lastError as Error;
   }
  get<T>(endpoint: string, config: ApiRequestConfig = {}) { return this.executeWithRetry<T>(this.buildUrl(endpoint, config.baseURL), { ...config, method: 'GET' }); }
  post<T>(endpoint: string, data?: unknown, config: ApiRequestConfig = {}) { return this.executeWithRetry<T>(this.buildUrl(endpoint, config.baseURL), { ...config, method: 'POST', body: data ? JSON.stringify(data) : undefined }); }
  put<T>(endpoint: string, data?: unknown, config: ApiRequestConfig = {}) { return this.executeWithRetry<T>(this.buildUrl(endpoint, config.baseURL), { ...config, method: 'PUT', body: data ? JSON.stringify(data) : undefined }); }
  patch<T>(endpoint: string, data?: unknown, config: ApiRequestConfig = {}) { return this.executeWithRetry<T>(this.buildUrl(endpoint, config.baseURL), { ...config, method: 'PATCH', body: data ? JSON.stringify(data) : undefined }); }
  delete<T>(endpoint: string, config: ApiRequestConfig = {}) { return this.executeWithRetry<T>(this.buildUrl(endpoint, config.baseURL), { ...config, method: 'DELETE' }); }
  async uploadFile<T>(endpoint: string, file: File, config: ApiRequestConfig = {}) {
    const url = this.buildUrl(endpoint, config.baseURL);
    const formData = new FormData(); formData.append('file', file);
    const headers = await this.buildHeaders({ ...config, skipAuth: config.skipAuth });
    // Remove content-type for multipart so browser sets boundary
    if (typeof (headers as Record<string, unknown>)['Content-Type'] !== 'undefined') {
      delete (headers as Record<string, unknown>)['Content-Type'];
    }
    return this.executeWithRetry<T>(url, { ...config, method: 'POST', body: formData, headers });
  }
  async uploadMultipleFiles<T>(endpoint: string, files: File[], config: ApiRequestConfig = {}) {
    const url = this.buildUrl(endpoint, config.baseURL);
    const formData = new FormData(); files.forEach((file, i) => formData.append(`files[${i}]`, file));
    const headers = await this.buildHeaders({ ...config, skipAuth: config.skipAuth });
    if (typeof (headers as Record<string, unknown>)['Content-Type'] !== 'undefined') {
      delete (headers as Record<string, unknown>)['Content-Type'];
    }
    return this.executeWithRetry<T>(url, { ...config, method: 'POST', body: formData, headers });
  }
}

export const apiClient = new ApiClient();
