import { useCallback, useEffect, useMemo, useState } from 'react';
import { storage } from '@/utils/api';
import { api } from '@/lib/api';
import { DashboardData, UserProfile, LeaderboardUser } from './types';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';

export function useDashboard(onLogout: () => void) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const normalizeAvatarUrl = useCallback((id?: string, avatarUrl?: string) => {
    if (id) return `/api/users/avatar?user-id=${encodeURIComponent(id)}`;
    return '/assets/images/default_avatar.png';
  }, []);

  const normalizeLeaderboard = useCallback((list: LeaderboardUser[] | undefined | null) => {
    if (!Array.isArray(list)) return [] as LeaderboardUser[];
    return list.map((u, idx) => {
      const normalizedId = (u as LeaderboardUser & { user_id?: string }).user_id || u.id;
      const googleAvatar = (u as { google_avatar_url?: string }).google_avatar_url || u.avatar_url;
      return {
        ...u,
        id: normalizedId,
        avatar_url: normalizeAvatarUrl(normalizedId, u.avatar_url),
        google_avatar_url: googleAvatar,
        avatarKey: Date.now() + idx,
      };
    });
  }, [normalizeAvatarUrl]);

  const normalizeProfile = useCallback((raw: UserProfile) => {
    if (!raw) return raw;
    const normalized = {
      ...raw,
      avatar_url: normalizeAvatarUrl(raw.id, raw.avatar_url),
      google_avatar_url: (raw as { google_avatar_url?: string }).google_avatar_url || raw.avatar_url,
      avatarKey: Date.now(),
    } as UserProfile & { user_top_rank?: LeaderboardUser[] };
    if ((raw as { user_top_rank?: LeaderboardUser[] }).user_top_rank) {
      normalized.user_top_rank = normalizeLeaderboard((raw as { user_top_rank?: LeaderboardUser[] }).user_top_rank);
    }
    return normalized;
  }, [normalizeAvatarUrl, normalizeLeaderboard]);

  const DASHBOARD_CACHE_KEY = 'pathlight_dashboard_cache';
  const CACHE_EXPIRY_MS = 5 * 60 * 1000;

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (loading) {
        setLoading(false);
        window.location.reload();
      }
    }, 20000);
    return () => clearTimeout(timeoutId);
  }, [loading]);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = storage.getToken();
        if (!token) {
          setLoading(false);
          onLogout();
          return;
        }
        const canUseStorage = typeof window !== 'undefined' && typeof window.localStorage?.getItem === 'function';
        if (canUseStorage) {
          try {
            const cached = window.localStorage.getItem(DASHBOARD_CACHE_KEY);
            if (cached) {
              const { data, timestamp } = JSON.parse(cached);
              if (Date.now() - timestamp < CACHE_EXPIRY_MS) {
                setUser(data.user);
                setDashboardData(data.dashboardData);
                setLoading(false);
                return;
              } else {
                window.localStorage.removeItem(DASHBOARD_CACHE_KEY);
              }
            }
          } catch (cacheError) {
            if (process.env.NODE_ENV === 'development') console.warn('Cache read error:', cacheError);
          }
        }
        const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Request timeout')), 30000));
        const response = await Promise.race([api.user.getDashboard(), timeoutPromise]);
        if (!response || typeof response !== 'object' || typeof (response as { status?: number }).status !== 'number') {
          throw new Error('Invalid API response');
        }
        const { status, data } = response as { status: number; data?: unknown };
        if (status === 401) { setLoading(false); onLogout(); return; }
        if (status !== 200) throw new Error(`API returned status ${status}`);
        const raw = data as DashboardData | { info?: UserProfile } | UserProfile | undefined;
        const userInfo: UserProfile = (raw && typeof raw === 'object' && 'info' in raw)
          ? (raw as { info?: UserProfile }).info || { email: '', name: '', id: '' }
          : (raw as UserProfile);
        const leaderboard = normalizeLeaderboard(userInfo.user_top_rank);
        const fullName = [userInfo.family_name, userInfo.given_name].filter(Boolean).join(' ') || (userInfo.email ? userInfo.email.split('@')[0] : 'User');
        const profileData: UserProfile = {
          id: userInfo.id || '',
          email: userInfo.email || '',
          name: fullName,
          given_name: userInfo.given_name,
          family_name: userInfo.family_name,
          avatar_url: normalizeAvatarUrl(userInfo.id, userInfo.avatar_url),
          avatarKey: Date.now(),
          remind_time: userInfo.remind_time,
          level: userInfo.level || 1,
          current_exp: userInfo.current_exp || 0,
          require_exp: userInfo.require_exp || 100,
          total_courses: userInfo.course_num || userInfo.total_courses || 0,
          completed_courses: userInfo.finish_course_num || userInfo.completed_courses || 0,
          total_quizzes: userInfo.quiz_num || userInfo.total_quizzes || 0,
          lesson_num: userInfo.lesson_num || 0,
          average_score: userInfo.average_quiz_score || userInfo.average_score || 0,
          rank: userInfo.rank || 1,
          user_num: userInfo.user_num || 1,
          user_top_rank: leaderboard,
        };
        const dashboardInfo: DashboardData = { info: { ...(profileData as UserProfile), user_top_rank: leaderboard } as UserProfile & { user_top_rank?: LeaderboardUser[] } };
        setDashboardData(dashboardInfo);
        setUser(profileData);
        setLoading(false);
        if (canUseStorage) {
          try { window.localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify({ user: profileData, dashboardData: dashboardInfo, timestamp: Date.now() })); } catch {}
        }
        if (!userInfo.remind_time) setTimeout(() => router.replace('/user/study-time-setup'), 100);
      } catch (error) {
        setLoading(false);
        if (error instanceof Error && error.message === 'Request timeout') {
          showToast.warning('⏱️ Trang web tải chậm. Vui lòng thử lại hoặc kiểm tra kết nối mạng.');
        } else {
          onLogout();
        }
      }
    };
    fetchProfile();
  }, [CACHE_EXPIRY_MS, onLogout, router]);

  return { user, dashboardData, loading };
}

export function useActivity() {
   const [activityData, setActivityData] = useState<Record<string, number>>({});
   const canUseStorage = typeof window !== 'undefined' && typeof window.localStorage?.getItem === 'function';

   useEffect(() => {
     if (!canUseStorage) return;
     try { const saved = window.localStorage.getItem('pathlight_activity_data'); if (saved) setActivityData(JSON.parse(saved)); } catch {}
   }, [canUseStorage]);

   useEffect(() => {
     if (Object.keys(activityData).length === 0) return;
     if (!canUseStorage) return;
     const timeoutId = setTimeout(() => { try { window.localStorage.setItem('pathlight_activity_data', JSON.stringify(activityData)); } catch {} }, 500);
     return () => clearTimeout(timeoutId);
   }, [activityData, canUseStorage]);

  const handleActivityClick = useCallback((dateKey: string, currentLevel: number) => {
    const newLevel = currentLevel >= 4 ? 0 : currentLevel + 1;
    const newActivityData = { ...activityData, [dateKey]: newLevel };
    setActivityData(newActivityData);
    if (!canUseStorage) return;
    if (window?.requestIdleCallback) window.requestIdleCallback(()=> window.localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData)));
    else setTimeout(()=> window.localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData)),0);
   }, [activityData, canUseStorage]);

   const generateYearActivityData = useMemo(() => (year: number) => {
      const activities = [] as { date: Date; level: number; count: number; isCurrentYear: boolean; dateKey: string }[];
      const startDate = new Date(year, 0, 1); const endDate = new Date(year, 11, 31);
      const firstDay = startDate.getDay(); const firstSunday = new Date(startDate); firstSunday.setDate(startDate.getDate() - firstDay);
      const lastDay = endDate.getDay(); const lastSaturday = new Date(endDate); lastSaturday.setDate(endDate.getDate() + (6 - lastDay));
      const targetDays = 53 * 7;
      for (let i=0;i<targetDays;i++){ const date = new Date(firstSunday); date.setDate(firstSunday.getDate()+i); const dateKey = date.toISOString().split('T')[0]; const isCurrentYear = date.getFullYear()===year; const activityLevel = activityData[dateKey] || 0; const contributionCount = activityLevel * 3; activities.push({ date, level: activityLevel, count: contributionCount, isCurrentYear, dateKey }); }
      return activities;
    }, [activityData]);

  const clearActivityData = () => { setActivityData({}); if (canUseStorage) window.localStorage.removeItem('pathlight_activity_data'); };

   return { activityData, handleActivityClick, generateYearActivityData, clearActivityData };
}
