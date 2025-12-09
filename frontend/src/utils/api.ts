import { cookieStorage } from './cookies';

// Centralized storage helpers (keep in this module per request)
export const storage = {
  getToken: (): string | null => cookieStorage.getToken(),
  setToken: (token: string, remember: boolean = false): void => cookieStorage.setToken(token, remember),
  removeToken: (): void => cookieStorage.removeToken(),
  isRemembered: (): boolean => cookieStorage.isRemembered(),
  getPendingEmail: (): string | null => cookieStorage.getPendingEmail(),
  setPendingEmail: (email: string): void => cookieStorage.setPendingEmail(email),
  removePendingEmail: (): void => cookieStorage.removePendingEmail(),
  get: (key: string): string | null => cookieStorage.get(key),
  set: (key: string, value: string): void => cookieStorage.set(key, value),
  remove: (key: string): void => cookieStorage.remove(key),
  clear: (): void => cookieStorage.clear(),
  isCookieEnabled: (): boolean => cookieStorage.isCookieEnabled(),
  isTokenExpiringSoon: (): boolean => cookieStorage.isTokenExpiringSoon(),
};

// Intentionally do not re-export API clients here to avoid circular deps with lib/api/http.
