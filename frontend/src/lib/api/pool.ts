// Central unified API Pool
// All frontend code should import from '@/lib/api/pool'
// Provides consistent base URL resolution, plural/singular endpoint fallback, and unified domains.

import { API_CONFIG } from '@/config/env';
import { api as legacyUtilsApi, storage as legacyStorage } from '@/utils/api';
import { api as modularApi } from '@/lib/api-client';
import { apiClient } from '@/lib/api/http';

// Simple fetch wrapper (fallback removed; endpoints standardized to /user/...)
async function fetchStandard(input: string, init?: RequestInit) {
  return fetch(input, init);
}

// Unified user domain
export const ApiPool = {
  storage: legacyStorage,
  http: {
    get: (url: string, init?: RequestInit) => fetchStandard(url, { ...init, method: 'GET' }),
    post: <B = unknown>(url: string, body?: B, init?: RequestInit) => fetchStandard(url, {
      ...init,
      method: 'POST',
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      headers: body instanceof FormData
        ? init?.headers
        : { 'Content-Type': 'application/json', ...(init?.headers || {}) }
    }),
    put: <B = unknown>(url: string, body?: B, init?: RequestInit) => fetchStandard(url, {
      ...init,
      method: 'PUT',
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      headers: body instanceof FormData
        ? init?.headers
        : { 'Content-Type': 'application/json', ...(init?.headers || {}) }
    }),
  },
  user: {
    info: () => legacyUtilsApi.user.getInfo(),
    dashboard: () => legacyUtilsApi.user.getDashboard(),
    changeInfo: (data: Record<string, unknown>) => legacyUtilsApi.user.updateProfile(data),
    avatar: {
      update: (file: File) => legacyUtilsApi.user.updateAvatar(file),
      get: (userId: string) => legacyUtilsApi.user.getAvatar(userId)
    },
    notifyTime: (data: { remind_time: string }) => legacyUtilsApi.user.setNotifyTime(data),
    activity: { save: () => legacyUtilsApi.user.activity.save() },
  },
  // Expose raw api clients for advanced needs
  raw: { legacyUtilsApi, modularApi, apiClient },
  config: { baseUrl: API_CONFIG.BASE_URL, directBackend: API_CONFIG.DIRECT_BACKEND }
};

export type ApiPoolType = typeof ApiPool;

export default ApiPool;
