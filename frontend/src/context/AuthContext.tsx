"use client";

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { storage } from '@/utils/api';
import userService from '@/services/user.service';
import { api } from '@/lib/api-client';
import { authUtils } from '@/utils/auth';

// Basic shape for user info consumed by UI (navbar, avatar, etc.)
export interface AuthUser {
  id?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  google_avatar_url?: string;
  avatarKey?: number;
  name?: string; // derived full name for convenience
  level?: number;
  current_exp?: number;
  require_exp?: number;
  remind_time?: string;
  rank?: number;
}

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;            // true while establishing session (initial) or refreshing user
  isAuthenticated: boolean;    // token present & (optimistically) not expired
  isRemembered: boolean;       // persisted via cookie flag
  login: (token: string, remember?: boolean) => Promise<AuthUser | null>; // set token + fetch user
  logout: () => void;
  refreshUser: () => Promise<AuthUser | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function tokenExpired(token: string | null) {
  if (!token) return true;
  const parts = token.split('.');
  if (parts.length !== 3) return false; // treat opaque tokens as not inspectable -> assume valid
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (!payload.exp) return false;
    return payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true); // initial loading
  const initRef = useRef(false);

  const readToken = () => storage.getToken();

  const buildUser = (raw: unknown): AuthUser | null => {
    if (!raw || typeof raw !== 'object') return null;
    const visited = new Set<unknown>();
    const candidateKeys = ['first_name','firstName','given_name','givenName'];
    const lastKeys = ['last_name','lastName','family_name','familyName'];
    const emailKeys = ['email','user_email','mail'];
    const avatarKeys = ['avatar_url','avatar','picture','photo'];
    const usernameKeys = ['username','user_name','name','display_name','full_name','fullName'];
    const levelKeys = ['level'];
    const currentExpKeys = ['current_exp','currentExp'];
    const requireExpKeys = ['require_exp','requireExp'];
    const remindKeys = ['remind_time','remindTime'];
    const rankKeys = ['rank','user_rank','userRank'];

    let first = '';
    let last = '';
    let email: string | undefined;
    let avatar_url: string | undefined;
    let google_avatar_url: string | undefined;
    let id: string | undefined;
    let derivedName: string | undefined;
    let level: number | undefined;
    let current_exp: number | undefined;
    let require_exp: number | undefined;
    let remind_time: string | undefined;
    let rank: number | undefined;

    const dfs = (obj: unknown) => {
      if (!obj || typeof obj !== 'object' || visited.has(obj)) return;
      visited.add(obj);
      const rec = obj as Record<string, unknown>;
      for (const [k,v] of Object.entries(rec)) {
        if (v && typeof v === 'object') dfs(v);
        const key = k.toString();
        if (!first && candidateKeys.includes(key) && typeof v === 'string') first = v;
        if (!last && lastKeys.includes(key) && typeof v === 'string') last = v;
        if (!email && emailKeys.includes(key) && typeof v === 'string') email = v;
        if (!avatar_url && avatarKeys.includes(key) && typeof v === 'string') {
          avatar_url = v;
          if (!google_avatar_url) google_avatar_url = v; // preserve as secondary fallback
        }
        if (!derivedName && usernameKeys.includes(key) && typeof v === 'string') derivedName = v;
        if (!id && key === 'id' && typeof v === 'string') id = v;
        if (level === undefined && levelKeys.includes(key) && typeof v === 'number') level = v;
        if (current_exp === undefined && currentExpKeys.includes(key) && typeof v === 'number') current_exp = v;
        if (require_exp === undefined && requireExpKeys.includes(key) && typeof v === 'number') require_exp = v;
        if (!remind_time && remindKeys.includes(key) && typeof v === 'string') remind_time = v;
        if (rank === undefined && rankKeys.includes(key) && typeof v === 'number') rank = v;
      }
    };
    dfs(raw);
    const nameComposite = [first, last].filter(Boolean).join(' ').trim();
    const name = nameComposite || derivedName || email || 'User';
    const normalizedAvatar = id ? `/api/users/avatar?user-id=${encodeURIComponent(id)}` : avatar_url;
    return { id, email, first_name: first, last_name: last, avatar_url: normalizedAvatar, google_avatar_url, name, level, current_exp, require_exp, remind_time, rank, avatarKey: Date.now() } as AuthUser & { avatarKey?: number };
  };

  const refreshUser = useCallback(async (): Promise<AuthUser | null> => {
    if (!readToken()) { setUser(null); return null; }
    try {
      // Prefer unified api.user.getInfo if available
  interface GetInfoResponse { status: number; error?: string; data?: unknown }
  type GetInfoFn = () => Promise<GetInfoResponse>;
  const maybeApi = api.user as unknown as { getInfo?: GetInfoFn };
  let res: GetInfoResponse | undefined = maybeApi.getInfo ? await maybeApi.getInfo() : undefined;
      if (!res || typeof res.status !== 'number') {
        res = await userService.getInfo();
      }
  if (res.status !== 200) { if (process.env.NODE_ENV === 'development') console.debug('[AuthContext] getInfo non-200', res.status, res.error); return null; }
  const built = buildUser(res.data);
  if (!built && process.env.NODE_ENV === 'development') console.debug('[AuthContext] Unable to build user from response', res.data);
      setUser(built);
      return built;
    } catch {
  if (process.env.NODE_ENV === 'development') console.debug('[AuthContext] getInfo failed');
      return null;
    }
  }, []);

  const login = useCallback(async (newToken: string, remember: boolean = false) => {
    storage.setToken(newToken, remember);
    setToken(newToken);
    // eagerly fetch user profile
    const u = await refreshUser();
    return u;
  }, [refreshUser]);

  const logout = useCallback(() => {
    authUtils.logout(); // this clears cookies/token per existing util
    setToken(null);
    setUser(null);
  }, []);

  // Initial bootstrap
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    const t = readToken();
    if (!t || tokenExpired(t)) {
      if (t) storage.removeToken();
      setToken(null);
      setUser(null);
      setLoading(false);
      return;
    }
    setToken(t);
    (async () => {
      await refreshUser();
      setLoading(false);
    })();
  }, [refreshUser]);

  // Periodic token validity check (every minute) similar to previous hook
  useEffect(() => {
    const interval = setInterval(() => {
      const t = readToken();
      if (!t || tokenExpired(t)) {
        logout();
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [logout]);

  // Revalidate on tab activation
  useEffect(() => {
    const handleVisibility = () => {
      if (!document.hidden) {
        const t = readToken();
        if (t && !tokenExpired(t) && !user) {
          refreshUser();
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [user, refreshUser]);

  const value: AuthContextValue = {
    token,
    user,
    loading,
    isAuthenticated: !!token && !tokenExpired(token),
    isRemembered: storage.isRemembered(),
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx) return ctx;

  // Fallback for routes rendered outside AuthProvider (e.g., admin pages)
  return {
    token: null,
    user: null,
    loading: false,
    isAuthenticated: false,
    isRemembered: false,
    login: async () => null,
    logout: () => {},
    refreshUser: async () => null,
  };
}
