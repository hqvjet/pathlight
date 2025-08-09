import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, storage } from '@/utils/api';
import { DashboardData, UserProfile } from './types';
import { useRouter } from 'next/navigation';

export function useDashboard(onLogout: () => void) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

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
        try {
          const cached = localStorage.getItem(DASHBOARD_CACHE_KEY);
          if (cached) {
            const { data, timestamp } = JSON.parse(cached);
            if (Date.now() - timestamp < CACHE_EXPIRY_MS) {
              setUser(data.user);
              setDashboardData(data.dashboardData);
              setLoading(false);
              return;
            } else {
              localStorage.removeItem(DASHBOARD_CACHE_KEY);
            }
          }
        } catch (cacheError) {
          if (process.env.NODE_ENV === 'development') console.warn('Cache read error:', cacheError);
        }
        const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Request timeout')), 8000));
        const response = await Promise.race([api.user.getDashboard(), timeoutPromise]) as { status: number; data?: unknown };
        if (response.status === 401) {
          setLoading(false); onLogout(); return; }
        if (response.status !== 200) throw new Error(`API returned status ${response.status}`);
        const data = response.data as DashboardData | { info?: UserProfile } | UserProfile;
        const userInfo = (data && typeof data === 'object' && 'info' in data) ? (data as any).info : data as UserProfile;
        const dashboardInfo: DashboardData = { info: userInfo as UserProfile & { user_top_rank?: any[] } };
        setDashboardData(dashboardInfo);
        const fullName = [userInfo.family_name, userInfo.given_name].filter(Boolean).join(' ') || (userInfo.email ? userInfo.email.split('@')[0] : 'User');
        const profileData: UserProfile = {
          id: userInfo.id || '',
            email: userInfo.email || '',
            name: fullName,
            given_name: userInfo.given_name,
            family_name: userInfo.family_name,
            avatar_url: userInfo.avatar_id || userInfo.avatar_url,
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
        };
        setUser(profileData);
        setLoading(false);
        try { localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify({ user: profileData, dashboardData: dashboardInfo, timestamp: Date.now() })); } catch {}
        if (!userInfo.remind_time) setTimeout(() => router.replace('/user/study-time-setup'), 100);
      } catch (error: any) {
        setLoading(false);
        if (error?.message === 'Request timeout') alert('⏱️ Trang web tải chậm. Vui lòng thử lại hoặc kiểm tra kết nối mạng.'); else onLogout();
      }
    };
    fetchProfile();
  }, [CACHE_EXPIRY_MS, onLogout, router]);

  return { user, dashboardData, loading };
}

export function useActivity(selectedYear: number) {
  const [activityData, setActivityData] = useState<Record<string, number>>({});

  useEffect(() => {
    try { const saved = localStorage.getItem('pathlight_activity_data'); if (saved) setActivityData(JSON.parse(saved)); } catch {}
  }, []);

  useEffect(() => {
    if (Object.keys(activityData).length === 0) return;
    const timeoutId = setTimeout(() => { try { localStorage.setItem('pathlight_activity_data', JSON.stringify(activityData)); } catch {} }, 500);
    return () => clearTimeout(timeoutId);
  }, [activityData]);

  const handleActivityClick = useCallback((dateKey: string, currentLevel: number) => {
    const newLevel = currentLevel >= 4 ? 0 : currentLevel + 1;
    const newActivityData = { ...activityData, [dateKey]: newLevel };
    setActivityData(newActivityData);
    if (window?.requestIdleCallback) window.requestIdleCallback(()=> localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData)));
    else setTimeout(()=> localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData)),0);
  }, [activityData]);

  const generateYearActivityData = useMemo(() => (year: number) => {
    const activities = [] as { date: Date; level: number; count: number; isCurrentYear: boolean; dateKey: string }[];
    const startDate = new Date(year, 0, 1); const endDate = new Date(year, 11, 31);
    const firstDay = startDate.getDay(); const firstSunday = new Date(startDate); firstSunday.setDate(startDate.getDate() - firstDay);
    const lastDay = endDate.getDay(); const lastSaturday = new Date(endDate); lastSaturday.setDate(endDate.getDate() + (6 - lastDay));
    const targetDays = 53 * 7;
    for (let i=0;i<targetDays;i++){ const date = new Date(firstSunday); date.setDate(firstSunday.getDate()+i); const dateKey = date.toISOString().split('T')[0]; const isCurrentYear = date.getFullYear()===year; const activityLevel = activityData[dateKey] || 0; const contributionCount = activityLevel * 3; activities.push({ date, level: activityLevel, count: contributionCount, isCurrentYear, dateKey }); }
    return activities;
  }, [activityData]);

  const clearActivityData = () => { setActivityData({}); localStorage.removeItem('pathlight_activity_data'); };

  return { activityData, handleActivityClick, generateYearActivityData, clearActivityData };
}
