import { useCallback, useEffect, useMemo, useState } from 'react';
import { storage } from '@/utils/api';
import { api } from '@/lib/api';
import { userApi, courseApi, quizApi } from '@/lib/api/user';
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
  const CACHE_EXPIRY_MS = 2 * 60 * 1000; // 2 minutes cache

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

        // Check cache
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

        // Fetch from 3 microservices in parallel
        const [userResponse, courseStatsResponse, quizStatsResponse] = await Promise.all([
          api.user.getDashboard(),
          courseApi.getStats().catch((err) => {
            console.warn('⚠️ Course stats failed:', err);
            return { status: 200, total_courses: 0, completed_courses: 0, total_lessons: 0 };
          }),
          quizApi.getStats().catch((err) => {
            console.warn('⚠️ Quiz stats failed (expected if not configured):', err);
            return { status: 200, total_quizzes: 0, completed_quizzes: 0, average_score: 0 };
          }),
        ]);

        console.log('📊 API Responses:', { userResponse, courseStatsResponse, quizStatsResponse });

        if (!userResponse || typeof (userResponse as { status?: number }).status !== 'number') {
          throw new Error('Invalid user API response');
        }

        const { status, data } = userResponse as { status: number; data?: unknown };
        if (status !== 200 || !data || typeof data !== 'object') {
          throw new Error('Failed to fetch user dashboard');
        }

        // Extract user info
        const userInfo = ('info' in data && data.info && typeof data.info === 'object') 
          ? data.info as Record<string, unknown>
          : data as Record<string, unknown>;

        // Extract stats from course and quiz services - check if wrapped in data object
        const courseStatsData = (courseStatsResponse as { data?: Record<string, unknown> }).data || courseStatsResponse as Record<string, unknown>;
        const quizStatsData = (quizStatsResponse as { data?: Record<string, unknown> }).data || quizStatsResponse as Record<string, unknown>;
        
        console.log('📊 Extracted Stats:', { 
          courseStatsData, 
          quizStatsData,
          courseStats_total: courseStatsData.total_courses,
          courseStats_lessons: courseStatsData.total_lessons
        });

        const leaderboard = normalizeLeaderboard(userInfo.user_top_rank as LeaderboardUser[] | undefined);
        const fullName = [userInfo.family_name, userInfo.given_name].filter(Boolean).join(' ') || 
                        ((userInfo.email as string)?.split('@')[0] || 'User');

        const profileData: UserProfile = {
          id: (userInfo.id as string) || '',
          email: (userInfo.email as string) || '',
          name: fullName,
          given_name: userInfo.given_name as string,
          family_name: userInfo.family_name as string,
          avatar_url: normalizeAvatarUrl(userInfo.id as string, userInfo.avatar_url as string),
          avatarKey: Date.now(),
          remind_time: userInfo.remind_time as string,
          level: (userInfo.level as number) || 1,
          current_exp: (userInfo.current_exp as number) || 0,
          require_exp: (userInfo.require_exp as number) || 100,
          streak: (userInfo.streak as number) || 0,
          // Course stats from course-service
          total_courses: (courseStatsData.total_courses as number) || 0,
          completed_courses: (courseStatsData.completed_courses as number) || 0,
          total_lessons: (courseStatsData.total_lessons as number) || 0,
          // Quiz stats from quiz-service
          total_quizzes: (quizStatsData.total_quizzes as number) || 0,
          completed_quizzes: (quizStatsData.completed_quizzes as number) || 0,
          // Ranking from user-service
          rank: (userInfo.rank as number) || 0,
          total_users: (userInfo.total_users as number) || 0,
          user_top_rank: leaderboard,
        };

        console.log('✅ Final Profile Data:', {
          total_courses: profileData.total_courses,
          completed_courses: profileData.completed_courses,
          total_lessons: profileData.total_lessons,
          total_quizzes: profileData.total_quizzes,
          level: profileData.level,
          rank: profileData.rank,
        });

        const dashboardInfo: DashboardData = { 
          info: { 
            ...profileData, 
            user_top_rank: leaderboard 
          } as UserProfile & { user_top_rank?: LeaderboardUser[] } 
        };

        setDashboardData(dashboardInfo);
        setUser(profileData);
        setLoading(false);

        // Cache the result
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

        // Check study time setup
        const skipped = storage.get('study_time_setup_completed') === 'true';
        if (!userInfo.remind_time && !skipped) {
          setTimeout(() => router.replace('/user/study-time-setup'), 100);
        }
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
      // Use local date format to match DB timezone (YYYY-MM-DD)
      const y = date.getFullYear();
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const d = String(date.getDate()).padStart(2, '0');
      const dateKey = `${y}-${m}-${d}`;
      const isCurrentYear = date.getFullYear() === year;
      const activityLevel = activityData[dateKey] || 0;
      const contributionCount = activityLevel * 3;
      activities.push({ date, level: activityLevel, count: contributionCount, isCurrentYear, dateKey });
    }
    return activities;
  }, [activityData]);

  return { activityData, generateYearActivityData, recordActivityEvent, loading };
}
