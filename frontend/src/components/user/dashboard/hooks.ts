import { useCallback, useEffect, useMemo, useState } from 'react';
import { storage } from '@/utils/api';
import { api } from '@/lib/api';
import { userApi } from '@/lib/api/user';
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
    if (avatarUrl) return avatarUrl;
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

  const DASHBOARD_CACHE_KEY = 'pathlight_dashboard_cache';
  const CACHE_EXPIRY_MS = 2 * 60 * 1000; // Reduce to 2 minutes for testing

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
        
        console.group('🔍 Dashboard API Response');
        console.log('Raw response:', response);
        console.log('Response type:', typeof response);
        console.log('Response keys:', response ? Object.keys(response as Record<string, unknown>) : 'null');
        console.log('Has status:', 'status' in (response as Record<string, unknown> || {}));
        console.log('Has data:', 'data' in (response as Record<string, unknown> || {}));
        console.groupEnd();
        
        if (!response || typeof response !== 'object' || typeof (response as { status?: number }).status !== 'number') {
          console.error('❌ Invalid API response structure');
          throw new Error('Invalid API response');
        }
        const { status, data } = response as { status: number; data?: unknown };
        
        console.group('📊 Dashboard Data Parsing');
        console.log('Status:', status);
        console.log('Data:', data);
        console.log('Data type:', typeof data);
        console.log('Data keys:', data && typeof data === 'object' ? Object.keys(data) : 'N/A');
        console.groupEnd();
        
        console.group('🔄 Data Structure Analysis');
        console.log('Has data:', !!data);
        console.log('Data type:', typeof data);
        
        let userInfo: UserProfile;
        
        if (data && typeof data === 'object') {
          const hasInfo = 'info' in data;
          console.log('Has info field:', hasInfo);
          
          // Check if data has 'info' field (backend structure)
          if (hasInfo && data.info && typeof data.info === 'object') {
            console.log('✅ Using info field from data');
            console.log('🔍 RAW INFO OBJECT:', data.info);
            console.log('Info keys:', Object.keys(data.info));
            console.log('Info values sample:', {
              id: (data.info as Record<string, unknown>).id,
              email: (data.info as Record<string, unknown>).email,
              total_courses: (data.info as Record<string, unknown>).total_courses,
              total_lessons: (data.info as Record<string, unknown>).total_lessons,
            });
            userInfo = data.info as UserProfile;
          } else {
            console.log('ℹ️  Using data directly (no info field)');
            console.log('🔍 RAW DATA OBJECT:', data);
            console.log('Data keys:', Object.keys(data));
            // Direct user profile data
            userInfo = data as UserProfile;
          }
        } else {
          console.error('❌ Invalid data structure');
          console.groupEnd();
          throw new Error('Invalid data structure');
        }
        console.groupEnd();
        
        console.group('📋 Parsed User Info');
        console.table({
          'ID': userInfo.id,
          'Email': userInfo.email,
          'Total Courses': userInfo.total_courses,
          'Course Num': userInfo.course_num,
          'Total Lessons': userInfo.total_lessons,
          'Lesson Num': userInfo.lesson_num,
          'Total Quizzes': userInfo.total_quizzes,
          'Quiz Num': userInfo.quiz_num,
          'Completed Courses': userInfo.completed_courses,
          'Finish Course Num': userInfo.finish_course_num,
          'Level': userInfo.level,
          'Current EXP': userInfo.current_exp,
          'Rank': userInfo.rank,
          'Total Users': userInfo.total_users,
          'User Num': userInfo.user_num,
        });
        console.groupEnd();
        
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
          total_courses: userInfo.total_courses ?? userInfo.course_num ?? 0,
          completed_courses: userInfo.completed_courses ?? userInfo.finish_course_num ?? 0,
          total_lessons: userInfo.total_lessons ?? userInfo.lesson_num ?? 0,
          total_quizzes: userInfo.total_quizzes ?? userInfo.quiz_num ?? 0,
          rank: userInfo.rank ?? 0,
          total_users: userInfo.total_users ?? userInfo.user_num ?? 0,
          user_top_rank: leaderboard,
        };
        
        console.group('✅ Final Profile Data');
        console.table({
          'Total Courses': profileData.total_courses,
          'Total Lessons': profileData.total_lessons,
          'Total Quizzes': profileData.total_quizzes,
          'Completed Courses': profileData.completed_courses,
          'Level': profileData.level,
          'Rank': profileData.rank,
        });
        console.groupEnd();
        
        const dashboardInfo: DashboardData = { 
          info: { 
            ...(profileData as UserProfile), 
            user_top_rank: leaderboard 
          } as UserProfile & { user_top_rank?: LeaderboardUser[] } 
        };
        
        setDashboardData(dashboardInfo);
        setUser(profileData);
        setLoading(false);
        
        if (canUseStorage) {
          try { 
            window.localStorage.setItem(
              DASHBOARD_CACHE_KEY, 
              JSON.stringify({ 
                data: { user: profileData, dashboardData: dashboardInfo }, 
                timestamp: Date.now() 
              })
            ); 
          } catch {}
        }
        const skipped = storage.get('study_time_setup_completed') === 'true';
        if (!userInfo.remind_time && !skipped) setTimeout(() => router.replace('/user/study-time-setup'), 100);
      } catch (error) {
        console.error('Dashboard fetch error:', error);
        setLoading(false);
        // Clear cache on error
        if (typeof window !== 'undefined') {
          try { window.localStorage.removeItem(DASHBOARD_CACHE_KEY); } catch {}
        }
        if (error instanceof Error && error.message === 'Request timeout') {
          showToast.warning('⏱️ Trang web tải chậm. Vui lòng thử lại hoặc kiểm tra kết nối mạng.');
        } else {
          showToast.error('❌ Không thể tải dữ liệu dashboard. Vui lòng thử lại.');
          console.error('Dashboard error details:', error);
        }
      }
    };
    fetchProfile();
  }, [CACHE_EXPIRY_MS, normalizeAvatarUrl, normalizeLeaderboard, onLogout, router]);

  return { user, dashboardData, loading };
}

export function useActivity() {
  const [activityData, setActivityData] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);

  const bucketLevel = useCallback((points: number) => {
    if (points <= 0) return 0;
    if (points === 1) return 1;
    if (points <= 3) return 2;
    if (points <= 6) return 3;
    return 4;
  }, []);

  const fetchActivity = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await userApi.getActivity(365);
      const items = (resp.data as { items?: Array<{ date: string; points: number }> })?.items || [];
      const mapped: Record<string, number> = {};
      items.forEach((it) => { mapped[it.date] = bucketLevel(it.points || 0); });
      setActivityData(mapped);
    } catch {
      // silent; keep existing state
    } finally {
      setLoading(false);
    }
  }, [bucketLevel]);

  useEffect(() => { fetchActivity(); }, [fetchActivity]);

  const recordActivityEvent = useCallback(async (event: string) => {
    try {
      await userApi.logActivity(event);
      await fetchActivity();
    } catch {
      // silent
    }
  }, [fetchActivity]);

  const generateYearActivityData = useMemo(() => (year: number) => {
    const activities: { date: Date; level: number; count: number; isCurrentYear: boolean; dateKey: string }[] = [];
    const startDate = new Date(year, 0, 1); const endDate = new Date(year, 11, 31);
    const firstDay = startDate.getDay(); const firstSunday = new Date(startDate); firstSunday.setDate(startDate.getDate() - firstDay);
    const lastDay = endDate.getDay(); const lastSaturday = new Date(endDate); lastSaturday.setDate(endDate.getDate() + (6 - lastDay));
    const targetDays = 53 * 7;
    for (let i = 0; i < targetDays; i++) {
      const date = new Date(firstSunday); date.setDate(firstSunday.getDate() + i);
      const dateKey = date.toISOString().split('T')[0];
      const isCurrentYear = date.getFullYear() === year;
      const activityLevel = activityData[dateKey] || 0;
      const contributionCount = activityLevel * 3;
      activities.push({ date, level: activityLevel, count: contributionCount, isCurrentYear, dateKey });
    }
    return activities;
  }, [activityData]);

  return { activityData, generateYearActivityData, recordActivityEvent, loading };
}
