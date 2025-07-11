'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { api, storage } from '@/utils/api';
import Avatar from '@/components/common/Avatar';
import { useRouter } from 'next/navigation';
import {
  BookOpenIcon,
  ClipboardListIcon,
  UserCircleIcon,
  DocumentTextIcon,
} from '@/components/icons';
import Layout from '@/components/common/Layout';

interface DashboardProps {
  onLogout: () => void;
}

interface UserProfile {
  id?: string;
  email: string;
  name: string;  // Required now
  given_name?: string;
  family_name?: string;
  avatar_url?: string;
  avatar_id?: string;
  remind_time?: string;
  level?: number;
  current_exp?: number;
  require_exp?: number;
  course_num?: number;
  total_courses?: number;
  completed_courses?: number;
  finish_course_num?: number;
  quiz_num?: number;
  total_quizzes?: number;
  lesson_num?: number;
  average_score?: number;
  average_quiz_score?: number;
  study_streak?: number;
  total_study_time?: number;
  rank?: number;
  user_num?: number;
  user_top_rank?: LeaderboardUser[];
}

interface LeaderboardUser {
  rank: number;
  name: string;
  level: number;
  experience: number;
  avatar_url?: string;
  id?: string; // Support user ID for S3 avatar lookup
  initials: string;
}

interface DashboardData {
  info: UserProfile & {
    user_top_rank?: LeaderboardUser[];
  };
  stats?: {
    study_hours?: number;
    total_courses?: number;
    completed_courses?: number;
    quiz_scores?: number;
  };
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [activityData, setActivityData] = useState<Record<string, number>>({});
  const router = useRouter();

  // Cache key for localStorage
  const DASHBOARD_CACHE_KEY = 'pathlight_dashboard_cache';
  const CACHE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes cache

  // Add a failsafe timeout to prevent infinite loading
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (loading) {
        console.warn('⚠️ Dashboard loading timeout reached, forcing reload...');
        setLoading(false);
        window.location.reload();
      }
    }, 20000); // 20 second absolute timeout

    return () => clearTimeout(timeoutId);
  }, [loading]);

  // Generate activity data for a specific year (using real data, not random)
  // Optimized generateYearActivityData with memoization
  const generateYearActivityData = useMemo(() => {
    return (year: number) => {
      const activities = [];
      const startDate = new Date(year, 0, 1); // January 1st of the year
      const endDate = new Date(year, 11, 31); // December 31st of the year
      
      // Find the first Sunday of the year (or before)
      const firstDay = startDate.getDay();
      const firstSunday = new Date(startDate);
      firstSunday.setDate(startDate.getDate() - firstDay);
      
      // Find the last Saturday after year end (or at year end)
      const lastDay = endDate.getDay();
      const lastSaturday = new Date(endDate);
      lastSaturday.setDate(endDate.getDate() + (6 - lastDay));
      
      // Calculate total days to generate - ensure we have exactly 53 weeks (371 days)
      const targetDays = 53 * 7;
      
      for (let i = 0; i < targetDays; i++) {
        const date = new Date(firstSunday);
        date.setDate(firstSunday.getDate() + i);
        
        const dateKey = date.toISOString().split('T')[0]; // Format: YYYY-MM-DD
        const isCurrentYear = date.getFullYear() === year;
        
        // Get activity level from stored data, default to 0
        const activityLevel = activityData[dateKey] || 0;
        const contributionCount = activityLevel * 3; // Simple calculation
        
        activities.push({
          date,
          level: activityLevel,
          count: contributionCount,
          isCurrentYear,
          dateKey
        });
      }
      
      return activities;
    };
  }, [activityData]); // Only recalculate when activityData changes

  // Function to handle clicking on activity squares (optimized with useCallback)
  const handleActivityClick = useCallback((dateKey: string, currentLevel: number) => {
    // Cycle through levels 0 -> 1 -> 2 -> 3 -> 4 -> 0
    const newLevel = currentLevel >= 4 ? 0 : currentLevel + 1;
    
    const newActivityData = {
      ...activityData,
      [dateKey]: newLevel
    };
    
    setActivityData(newActivityData);
    
    // Save to localStorage asynchronously for better performance
    if (typeof window !== 'undefined') {
      if (window.requestIdleCallback) {
        window.requestIdleCallback(() => {
          localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData));
        });
      } else {
        setTimeout(() => {
          localStorage.setItem('pathlight_activity_data', JSON.stringify(newActivityData));
        }, 0);
      }
    }
    
    // Optional: Save to backend
    // api.user.activity.save({ date: dateKey, level: newLevel });
  }, [activityData]);

  // Clear activity data (with cache clearing)
  const clearActivityData = () => {
    setActivityData({});
    if (typeof window !== 'undefined') {
      localStorage.removeItem('pathlight_activity_data');
    }
    // Optional: Clear from backend
    // api.user.activity.clear();
  };

  // Force refresh functionality (can be used later)
  // const refreshDashboard = useCallback(async () => {
  //   try {
  //     localStorage.removeItem(DASHBOARD_CACHE_KEY);
  //     setLoading(true);
  //     window.location.reload();
  //   } catch (error) {
  //     console.error('Failed to refresh dashboard:', error);
  //   }
  // }, []);

  // Load activity data from backend (optional)
  const loadActivityFromBackend = async () => {
    try {
      const response = await api.user.activity.get(selectedYear);
      if (response.status === 200) {
        const backendData = (response.data as any)?.activityData || {};
        setActivityData(backendData);
        localStorage.setItem('pathlight_activity_data', JSON.stringify(backendData));
        alert('✅ Activity data loaded from server!');
      }
    } catch (error) {
      console.error('Failed to load activity data from backend:', error);
      alert('❌ Failed to load activity data from server');
    }
  };

  // Save activity data to backend (optional)
  const saveActivityToBackend = async () => {
    try {
      const response = await api.user.activity.saveBatch(activityData);
      if (response.status === 200) {
        alert('✅ Activity data saved to server!');
      }
    } catch (error) {
      console.error('Failed to save activity data to backend:', error);
      alert('❌ Failed to save activity data to server');
    }
  };

  // Load activity data from localStorage on component mount (optimized)
  useEffect(() => {
    // Use requestIdleCallback for non-critical localStorage loading
    const loadActivityData = () => {
      try {
        const saved = localStorage.getItem('pathlight_activity_data');
        if (saved) {
          setActivityData(JSON.parse(saved));
        }
      } catch (error) {
        console.error('Failed to load activity data from localStorage:', error);
      }
    };

    // Ensure we're in browser environment
    if (typeof window !== 'undefined') {
      if (window.requestIdleCallback) {
        window.requestIdleCallback(loadActivityData);
      } else {
        setTimeout(loadActivityData, 0);
      }
    }
  }, []);

  // Save activity data to localStorage whenever it changes (debounced)
  useEffect(() => {
    if (typeof window !== 'undefined' && Object.keys(activityData).length > 0) {
      const timeoutId = setTimeout(() => {
        try {
          localStorage.setItem('pathlight_activity_data', JSON.stringify(activityData));
        } catch (error) {
          console.error('Failed to save activity data:', error);
        }
      }, 500); // Debounce saves

      return () => clearTimeout(timeoutId);
    }
  }, [activityData]);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        console.log('🚀 Dashboard fetchProfile started');
        const token = storage.getToken();
        if (!token) {
          console.log('❌ No token found, redirecting to login');
          setLoading(false);
          onLogout();
          return;
        }

        console.log('🔑 Token found, checking cache...');
        // Try to load from cache first
        try {
          const cached = localStorage.getItem(DASHBOARD_CACHE_KEY);
          if (cached) {
            const { data, timestamp } = JSON.parse(cached);
            if (Date.now() - timestamp < CACHE_EXPIRY_MS) {
              console.log('📱 Loading dashboard from cache');
              setUser(data.user);
              setDashboardData(data.dashboardData);
              setLoading(false);
              return; // Use cached data
            } else {
              console.log('⏰ Cache expired, removing...');
              localStorage.removeItem(DASHBOARD_CACHE_KEY);
            }
          }
        } catch (cacheError) {
          console.warn('Cache read error:', cacheError);
        }
        
        // Add timeout to the API call for better UX
        console.log('🌐 Making API call...');
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), 8000); // 8 seconds timeout
        });
        
        console.log('🌐 Fetching fresh dashboard data...');
        const response = await Promise.race([
          api.user.getDashboard(),
          timeoutPromise
        ]) as any;
        
        console.log('📡 API response received:', response.status);
        
        if (response.status === 401) {
          console.log('🔐 Unauthorized, logging out');
          setLoading(false);
          onLogout();
          return;
        }
        
        if (response.status !== 200) {
          throw new Error(`API returned status ${response.status}`);
        }
        
        console.log('✅ Processing dashboard data...');
        const data = response.data as DashboardData | { info?: UserProfile } | UserProfile;
        const userInfo = (data && typeof data === 'object' && 'info' in data) ? data.info : data as UserProfile;
        
        // Store the full dashboard data
        const dashboardInfo: DashboardData = {
          info: userInfo as UserProfile & { user_top_rank?: LeaderboardUser[] }
        };
        setDashboardData(dashboardInfo);
      
        
        // Combine name from given_name and family_name (optimized)
        const fullName = [userInfo.family_name, userInfo.given_name]
          .filter(Boolean)
          .join(' ') || (userInfo.email ? userInfo.email.split('@')[0] : 'User');
        
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
        
        console.log('👤 Setting user data...');
        setUser(profileData);
        setLoading(false);

        // Cache the result for future use
        try {
          const cacheData = {
            user: profileData,
            dashboardData: dashboardInfo,
            timestamp: Date.now()
          };
          localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(cacheData));
          console.log('💾 Dashboard data cached successfully');
        } catch (cacheError) {
          console.warn('Cache write error:', cacheError);
        }
        
        console.log('🎉 Dashboard loading completed successfully');
        
        // Navigate to study-time-setup in background if needed
        if (!userInfo.remind_time) {
          setTimeout(() => router.replace('/user/study-time-setup'), 100);
        }
      } catch (error) {
        console.error('💥 Dashboard fetch error:', error);
        setLoading(false);
        
        // Show error message instead of immediate logout for better UX
        if (error instanceof Error && error.message === 'Request timeout') {
          console.warn('⏱️ Dashboard loading timed out, showing retry option...');
          // Show timeout error but don't auto-retry to prevent infinite loops
          alert('⏱️ Trang web tải chậm. Vui lòng thử lại hoặc kiểm tra kết nối mạng.');
        } else {
          console.error('🚨 Unexpected error, logging out:', error);
          onLogout();
        }
      }
    };
    fetchProfile();
    // eslint-disable-next-line
  }, []);

  // Remove duplicate localStorage loading (already handled above)
  // This was causing double loading and potential conflicts

  // Logout handler (currently unused but may be needed later)
  // const handleLogout = () => {
  //   try {
  //     localStorage.removeItem(DASHBOARD_CACHE_KEY);
  //     localStorage.removeItem('pathlight_activity_data');
  //   } catch (error) {
  //     console.warn('Failed to clear cache on logout:', error);
  //   }
  //   storage.removeToken();
  //   onLogout();
  // };

  // Helper function to handle test API calls (optimized)
  const handleTestAPI = useCallback(async (apiCall: () => Promise<any>) => {
    try {
      console.log('🧪 Making test API call...');
      const response = await apiCall();
      
      console.log('📤 API Response:', response);
      
      if (response.status === 200) {
        alert(`✅ ${response.message || 'Success!'}`);
        // Force refresh by clearing cache and reloading
        localStorage.removeItem(DASHBOARD_CACHE_KEY);
        setTimeout(() => window.location.reload(), 500);
      } else {
        console.error('❌ API Error:', response);
        alert(`❌ Error ${response.status}: ${response.message || response.error || 'Unknown error occurred'}`);
      }
    } catch (error) {
      console.error('🚨 Test API error:', error);
      
      // More detailed error information
      let errorMessage = '❌ Network error occurred';
      if (error instanceof Error) {
        errorMessage = `❌ ${error.message}`;
      }
      
      alert(errorMessage);
    }
  }, []);

  // Helper function to view level system information
  const handleViewLevelInfo = async () => {
    try {
      const response = await api.user.test.getLevelSystemInfo();
      
      if (response.status === 200) {
        const data = response.data as any; // Type assertion for level system data
        const levels = data.level_system.levels.slice(0, 10); // Show first 10 levels
        const info = levels.map((l: { level: number; required_exp: number; exp_to_next: number }) => 
          `Level ${l.level}: ${l.required_exp} exp (${l.exp_to_next} to next)`
        ).join('\n');
        
        alert(`📊 Level System Info:\n\n${info}\n\n...and more (exponential growth after level ${data.level_system.max_predefined_level})`);
      } else {
        alert(`❌ ${response.message || 'Error getting level info'}`);
      }
    } catch (error) {
      console.error('Level info error:', error);
      alert('❌ Network error occurred');
    }
  };

  // Memoize layout user props to prevent unnecessary re-renders
  const layoutUser = useMemo(() => {
    if (!user) return { avatar_url: '', name: '', email: '' };
    return {
      avatar_url: user.avatar_url || '',
      name: user.name,
      email: user.email,
      avatarKey: Date.now() // Add timestamp to force avatar refresh
    };
  }, [user?.avatar_url, user?.name, user?.email]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-lg text-gray-600 mb-2">Đang tải thông tin...</div>
          <div className="text-sm text-gray-400">Vui lòng đợi trong giây lát</div>
          
          {/* Progress bar */}
          <div className="mt-4 w-64 bg-gray-200 rounded-full h-2 mx-auto">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }}></div>
          </div>
          
          {/* Quick actions while loading */}
          <div className="mt-6 space-y-2">
            <button 
              onClick={() => {
                localStorage.removeItem(DASHBOARD_CACHE_KEY);
                window.location.reload();
              }} 
              className="text-blue-600 hover:text-blue-800 text-sm underline block mx-auto"
            >
              Tải lại trang nếu quá lâu
            </button>
            <button 
              onClick={() => {
                localStorage.clear();
                window.location.href = '/auth/login';
              }} 
              className="text-red-600 hover:text-red-800 text-xs underline block mx-auto"
            >
              Đăng nhập lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Early return if no user data to prevent rendering issues
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-lg text-gray-600 mb-4">Không tìm thấy thông tin người dùng</div>
          <button 
            onClick={() => window.location.href = '/auth/login'} 
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            Đăng nhập lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <Layout 
      title="Trang Chủ" 
      user={layoutUser}
    >
      {/* Dashboard Content */}
      <div className="p-4 sm:p-6 lg:p-8 min-h-screen">
        <div className="max-w-7xl mx-auto">
          {/* Top Stats Row - Course Statistics */}
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
            {/* Total Courses */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-orange-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <BookOpenIcon className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-orange-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-bold text-gray-900 truncate">{user.total_courses}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Tổng Số Khóa Học</p>
                </div>
              </div>
            </div>

            {/* Total Quizzes */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <ClipboardListIcon className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-blue-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-bold text-gray-900 truncate">{user.total_quizzes}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Tổng Số Quiz</p>
                </div>
              </div>
            </div>

            {/* Total Lessons */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <DocumentTextIcon className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-purple-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">{user.lesson_num}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Tổng Số Bài Học</p>
                </div>
              </div>
            </div>

            {/* Completed Courses */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-green-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">{user.completed_courses}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Số Khóa Học Hoàn Thành</p>
                </div>
              </div>
            </div>
          </div>

          {/* Second Stats Row - User Statistics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
            {/* Experience */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-red-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">{(user.current_exp || 0).toLocaleString()}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Kinh nghiệm</p>
                </div>
              </div>
            </div>

            {/* Level */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-green-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">Level {user.level}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Cấp độ</p>
                </div>
              </div>
            </div>

            {/* Rank */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-yellow-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">{user.rank}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Bậc Xếp Hạng Của Bạn</p>
                </div>
              </div>
            </div>

            {/* Total Users */}
            <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-lg shadow-sm border border-gray-100">
              <div className="flex items-center">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-indigo-100 rounded-lg flex items-center justify-center mr-2 sm:mr-3 lg:mr-4 flex-shrink-0">
                  <UserCircleIcon className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-indigo-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">{user.user_num}</h3>
                  <p className="text-xs sm:text-sm text-gray-600">Xếp Hạng Người Dùng</p>
                </div>
              </div>
            </div>
          </div>

          {/* Progress and Activity Row - Responsive */}
          <div className="grid grid-cols-1 lg:grid-cols-10 gap-4 sm:gap-6 mb-4 sm:mb-6">
            {/* User Profile Card with Progress */}
            <div className="lg:col-span-3 bg-gray-800 text-white rounded-lg p-4 sm:p-6">
              <div className="flex items-center space-x-3 sm:space-x-4 mb-4 sm:mb-6">
                <Avatar 
                  key={`dashboard-profile-${user.avatar_url || 'default'}-${Date.now()}`}
                  user={user} 
                  size={80} 
                  className="w-16 h-16 sm:w-20 sm:h-20 flex-shrink-0" 
                  displayName={user.name || (user.email ? user.email.split('@')[0] : 'User')}
                  showInitialsFallback={true}
                />
                <div className="flex-1 min-w-0">
                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-1 truncate">
                    {(() => {
                      if (user.name) {
                        return user.name;
                      } else if (user.email) {
                        return user.email.split('@')[0];
                      }
                      return 'User';
                    })()}
                  </h3>
                  <p className="text-gray-300 text-sm truncate">{user.email || 'email@example.com'}</p>
                </div>
              </div>
              <div className="w-full">
                <div className="flex justify-between text-sm mb-2 text-gray-300">
                  <span>Tiến trình học tập</span>
                  <span className="text-white font-medium">
                    {user.total_courses > 0 ? Math.round((user.completed_courses / user.total_courses) * 100) : 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
                  <div 
                    className="bg-green-500 h-3 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${user.total_courses > 0 ? Math.round((user.completed_courses / user.total_courses) * 100) : 0}%` 
                    }}
                  ></div>
                </div>
                
                {/* Level Progress */}
                <div className="w-full">
                  <div className="flex justify-between text-sm mb-2 text-gray-300">
                    <span>Level {user.level}</span>
                    <span className="text-yellow-400 font-medium">
                      {(() => {
                        const currentExp = user.current_exp || 0;
                        const nextLevelExp = user.require_exp || 100;
                        // Simple percentage calculation for display
                        const progressPercentage = Math.min(100, (currentExp / nextLevelExp) * 100);
                        return `${Math.round(progressPercentage)}%`;
                      })()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-3">
                    {(() => {
                      const currentExp = user.current_exp || 0;
                      const nextLevelExp = user.require_exp || 100;
                      const estimatedCurrentLevelStart = Math.max(0, nextLevelExp - Math.round(nextLevelExp * 0.4)); // Rough estimate
                      const progressExp = Math.max(0, currentExp - estimatedCurrentLevelStart);
                      const levelExpRange = nextLevelExp - estimatedCurrentLevelStart;
                      const progressPercentage = Math.min(100, (progressExp / levelExpRange) * 100);
                      
                      return (
                        <div 
                          className="bg-gradient-to-r from-yellow-400 to-yellow-500 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${progressPercentage}%` }}
                        ></div>
                      );
                    })()}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>{(user.current_exp || 0).toLocaleString()} exp</span>
                    <span>{(user.require_exp || 100).toLocaleString()} exp cho Level {(user.level || 1) + 1}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Activity Heatmap */}
            <div className="lg:col-span-7 bg-[#0d1117] rounded-lg shadow-sm p-4 sm:p-6 border border-gray-700">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <div>
                  <h3 className="text-sm sm:text-base font-medium text-gray-300">
                    {(() => {
                      const yearActivityData = generateYearActivityData(selectedYear);
                      const totalContributions = yearActivityData
                        .filter(activity => activity.isCurrentYear)
                        .reduce((sum, activity) => sum + activity.count, 0);
                      const activeDays = yearActivityData
                        .filter(activity => activity.isCurrentYear && activity.level > 0)
                        .length;
                      return `${totalContributions} hoạt động trong ${activeDays} ngày năm ${selectedYear}`;
                    })()}
                  </h3>
                </div>
                <div className="flex items-center space-x-2">
                  <select 
                    value={selectedYear} 
                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                    className="px-2 sm:px-3 py-1 border border-gray-600 rounded-md text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-gray-800 text-white"
                  >
                    {[2025, 2024, 2023, 2022, 2021].map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Activity grid container */}
              <div className="bg-[#161b22] rounded-lg p-3 overflow-x-auto">
                <div className="flex gap-2">
                  {/* Day labels */}
                  <div className="hidden sm:flex flex-col justify-around text-xs text-gray-500 py-1 flex-shrink-0" style={{ height: '127px' }}>
                    <div className="h-3"></div>
                    <div className="h-3"></div>
                    <div className="h-3 flex items-center">T2</div>
                    <div className="h-3"></div>
                    <div className="h-3 flex items-center">T4</div>
                    <div className="h-3"></div>
                    <div className="h-3 flex items-center">T6</div>
                    <div className="h-3"></div>
                  </div>
                  
                  {/* Activity content with month labels */}
                  <div className="flex-1" style={{ minWidth: '800px' }}>
                    {/* Month labels */}
                    <div className="mb-3 hidden sm:block">
                      <div className="grid grid-cols-12 text-xs text-gray-400 px-1">
                        <div className="text-center">Th1</div>
                        <div className="text-center">Th2</div>
                        <div className="text-center">Th3</div>
                        <div className="text-center">Th4</div>
                        <div className="text-center">Th5</div>
                        <div className="text-center">Th6</div>
                        <div className="text-center">Th7</div>
                        <div className="text-center">Th8</div>
                        <div className="text-center">Th9</div>
                        <div className="text-center">Th10</div>
                        <div className="text-center">Th11</div>
                        <div className="text-center">Th12</div>
                      </div>
                    </div>
                    
                    {/* Activity squares grid */}
                    <div className="grid grid-rows-7 grid-flow-col gap-1" style={{ 
                      gridTemplateColumns: 'repeat(53, 1fr)',
                      height: '108px'
                    }}>
                      {(() => {
                        const yearActivityData = generateYearActivityData(selectedYear);
                        
                        return yearActivityData.map((activity, i) => {
                          // GitHub-like colors với theme tối
                          const colors = [
                            '#161b22',  // 0 hoạt động - dark background
                            '#0e4429',  // 1 hoạt động - dark green  
                            '#006d32',  // 2 hoạt động - medium green
                            '#26a641',  // 3 hoạt động - bright green
                            '#39d353'   // 4 hoạt động - brightest green
                          ];
                          
                          const isCurrentYear = activity.isCurrentYear;
                          // Ô không trong năm thì transparent
                          const backgroundColor = isCurrentYear ? colors[activity.level] : 'transparent';
                          const borderColor = isCurrentYear ? '#30363d' : 'transparent';
                          
                          return (
                            <div 
                              key={i} 
                              className={`rounded-sm transition-all ${isCurrentYear ? 'cursor-pointer hover:ring-2 hover:ring-blue-400 hover:scale-110' : ''}`}
                              style={{ 
                                backgroundColor,
                                border: `1px solid ${borderColor}`,
                                minWidth: '10px',
                                minHeight: '10px'
                              }}
                              onClick={() => {
                                if (isCurrentYear) {
                                  handleActivityClick(activity.dateKey, activity.level);
                                }
                              }}
                              title={isCurrentYear ? 
                                `${activity.date.toLocaleDateString('vi-VN')} - Level ${activity.level} (Click để thay đổi)` : 
                                activity.date.toLocaleDateString('vi-VN')
                              }
                            />
                          );
                        });
                      })()}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Legend */}
              <div className="flex justify-between items-center mt-4">
                <div className="text-xs text-gray-300 hidden sm:block">
                  Click vào ô để thay đổi mức độ hoạt động (0-4)
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Không</span>
                  <div className="flex space-x-1">
                    <div 
                      className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-sm cursor-pointer hover:scale-110 transition-transform" 
                      style={{ backgroundColor: '#161b22' }}
                      title="Level 0 - Không hoạt động"
                    ></div>
                    <div 
                      className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-sm cursor-pointer hover:scale-110 transition-transform" 
                      style={{ backgroundColor: '#0e4429' }}
                      title="Level 1 - Ít hoạt động"
                    ></div>
                    <div 
                      className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-sm cursor-pointer hover:scale-110 transition-transform" 
                      style={{ backgroundColor: '#006d32' }}
                      title="Level 2 - Hoạt động vừa"
                    ></div>
                    <div 
                      className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-sm cursor-pointer hover:scale-110 transition-transform" 
                      style={{ backgroundColor: '#26a641' }}
                      title="Level 3 - Hoạt động nhiều"
                    ></div>
                    <div 
                      className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-sm cursor-pointer hover:scale-110 transition-transform" 
                      style={{ backgroundColor: '#39d353' }}
                      title="Level 4 - Hoạt động rất nhiều"
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500">Nhiều</span>
                </div>
              </div>
            </div>
          </div>

          {/* Leaderboard Section - Responsive */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Top 3 Leaderboard */}
            <div className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg shadow-lg p-4 sm:p-6 order-2 lg:order-1">
              <h3 className="text-lg font-semibold text-white mb-4 sm:mb-6 text-center">🏆 Top Bảng Xếp Hạng</h3>
              
              {dashboardData?.info?.user_top_rank && dashboardData.info.user_top_rank.length > 0 ? (
                <div className="flex justify-center items-end gap-1 mb-6">
                  {/* Show top 3 users with proper podium hierarchy */}
                  {(() => {
                    const topUsers = dashboardData.info.user_top_rank.slice(0, 3);
                    
                    // Podium configuration: 2nd - 1st - 3rd
                    const positions = [
                      { // Rank 2 - Left
                        rank: 2, 
                        height: 'h-32', 
                        avatarSize: 'w-16 h-16', 
                        avatarPixelSize: 60,
                        bgGradient: 'from-gray-300 to-gray-500',
                        order: 0,
                        borderColor: 'border-gray-400',
                        nameTag: 'bg-gray-700'
                      },
                      { // Rank 1 - Center (highest)
                        rank: 1, 
                        height: 'h-40', 
                        avatarSize: 'w-20 h-20', 
                        avatarPixelSize: 76,
                        bgGradient: 'from-yellow-400 to-yellow-600',
                        crown: true, 
                        order: 1,
                        borderColor: 'border-yellow-400',
                        nameTag: 'bg-yellow-700'
                      },
                      { // Rank 3 - Right
                        rank: 3, 
                        height: 'h-28', 
                        avatarSize: 'w-14 h-14', 
                        avatarPixelSize: 52,
                        bgGradient: 'from-orange-400 to-orange-600',
                        order: 2,
                        borderColor: 'border-orange-400',
                        nameTag: 'bg-orange-700'
                      }
                    ];

                    return topUsers.map((user) => {
                      const position = positions.find(p => p.rank === user.rank);
                      if (!position) return null;
                      
                      return (
                        <div key={user.rank} className="flex flex-col items-center w-[100px]" style={{ order: position.order }}>
                          {/* Crown for rank 1 */}
                          {position.crown && (
                            <div className="mb-1">
                              <span className="text-2xl">👑</span>
                            </div>
                          )}
                          
                          {/* User Avatar */}
                          <div className="relative mb-2">
                            <div className={`${position.avatarSize} rounded-full border-4 ${position.borderColor} shadow-lg bg-white p-0.5`}>
                              <Avatar 
                                key={`leaderboard-${user.rank}-${user.avatar_url || user.id || 'default'}-${Date.now()}`}
                                user={{
                                  id: user.id,
                                  avatar_url: user.avatar_url || ''
                                }} 
                                size={position.avatarPixelSize} 
                                className="w-full h-full rounded-full object-cover"
                                displayName={user.name || 'User'}
                                showInitialsFallback={false}
                              />
                            </div>
                          </div>
                          
                          {/* User Name Tag */}
                          <div className={`${position.nameTag} text-white px-3 py-1 rounded-md text-xs font-semibold mb-1 max-w-[90px]`}>
                            <div className="truncate text-center">
                              {user.name || 'User'}
                            </div>
                          </div>
                          
                          {/* Podium Base */}
                          <div className={`${position.height} w-full bg-gradient-to-t ${position.bgGradient} rounded-t-lg flex flex-col justify-end items-center relative shadow-lg pb-3`}>
                            <div className="text-white text-2xl font-bold mb-1">
                              {user.level}
                            </div>
                            <div className="text-white text-xs font-medium">
                              Level
                            </div>
                            
                            {/* Rank Number Badge */}
                            <div className="absolute top-2 right-2 w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs font-bold">{user.rank}</span>
                            </div>
                          </div>
                        </div>
                      );
                    }).filter(Boolean);
                  })()}
                  
                  {/* Empty spots for missing users */}
                  {Array.from({ length: Math.max(0, 3 - dashboardData.info.user_top_rank.length) }).map((_, index) => {
                    const emptyPositions = [
                      { height: 'h-32', avatarSize: 'w-16 h-16', order: 0, bgGradient: 'from-gray-300 to-gray-500' },  
                      { height: 'h-40', avatarSize: 'w-20 h-20', order: 1, bgGradient: 'from-yellow-400 to-yellow-600' },
                      { height: 'h-28', avatarSize: 'w-14 h-14', order: 2, bgGradient: 'from-orange-400 to-orange-600' }
                    ];
                    
                    const startIndex = dashboardData.info.user_top_rank.length;
                    const position = emptyPositions[startIndex + index];
                    
                    return (
                      <div key={`empty-${index}`} className="flex flex-col items-center w-[100px] opacity-50" style={{ order: position.order }}>
                        <div className="mb-1">
                          <span className="text-2xl opacity-30">👤</span>
                        </div>
                        
                        {/* Empty Avatar Slot */}
                        <div className="relative mb-2">
                          <div className={`${position.avatarSize} rounded-full border-4 border-white/30 shadow-lg bg-white/10 p-0.5`}>
                            <div className="w-full h-full rounded-full bg-gray-300/30 flex items-center justify-center">
                              <svg className="w-6 h-6 text-gray-400/50" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z" />
                              </svg>
                            </div>
                          </div>
                        </div>
                        
                        {/* Empty Name Tag */}
                        <div className="bg-gray-700/50 text-white/70 px-3 py-1 rounded-md text-xs font-semibold mb-1 max-w-[90px]">
                          <div className="truncate text-center">Empty</div>
                        </div>
                        
                        {/* Empty Podium */}
                        <div className={`${position.height} w-full bg-gradient-to-t ${position.bgGradient} opacity-30 rounded-t-lg flex flex-col justify-end items-center shadow-lg pb-3`}>
                          <div className="text-white/50 text-2xl font-bold mb-1">--</div>
                          <div className="text-white/50 text-xs font-medium">Level</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center text-white">
                  <p className="text-lg mb-4">Chưa có dữ liệu bảng xếp hạng</p>
                </div>
              )}
            </div>

            {/* Full Leaderboard Table */}
            <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 order-1 lg:order-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 sm:mb-6">📊 Xếp Hạng 4-10</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Xếp Hạng</th>
                      <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Avatar</th>
                      <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Người Dùng</th>
                      <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Level</th>
                      <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Kinh Nghiệm</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {dashboardData?.info?.user_top_rank ? 
                      dashboardData.info.user_top_rank.slice(3, 10).map((user) => {
                        // Row styling - no special styling for ranks 4+
                        const getRowStyling = () => {
                          return 'hover:bg-gray-50';
                        };
                        
                        return (
                          <tr key={user.rank} className={`transition-colors ${getRowStyling()}`}>
                            <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-sm font-bold text-gray-900 mr-2">#{user.rank}</span>
                                <span className="text-sm font-bold text-gray-900">{user.rank}</span>
                              </div>
                            </td>
                            <td className="px-3 sm:px-4 py-3 whitespace-nowrap hidden sm:table-cell">
                              <Avatar 
                                user={user} 
                                size={40} 
                                className="w-10 h-10 shadow-sm"
                                displayName={user.name || 'User'}
                                showInitialsFallback={false}
                              />
                            </td>
                            <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                              <div className="flex items-center sm:hidden">
                                <Avatar 
                                  user={user} 
                                  size={32} 
                                  className="w-8 h-8 mr-3 shadow-sm"
                                  displayName={user.name || 'User'}
                                  showInitialsFallback={false}
                                />
                              </div>
                              <div className="text-sm font-medium text-gray-900">{user.name || 'User'}</div>
                            </td>
                            <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Level {user.level}
                              </span>
                            </td>
                            <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                              <div className="text-sm text-gray-900 font-medium">
                                {(user.experience || 0).toLocaleString()} exp
                              </div>
                            </td>
                          </tr>
                        );
                      }) : 
                      // Fallback data if no leaderboard available
                      Array.from({ length: 5 }, (_, index) => (
                        <tr key={index} className="hover:bg-gray-50 transition-colors animate-pulse">
                          <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-6 h-6 bg-gray-200 rounded mr-2"></div>
                              <div className="w-4 h-4 bg-gray-200 rounded"></div>
                            </div>
                          </td>
                          <td className="px-3 sm:px-4 py-3 whitespace-nowrap hidden sm:table-cell">
                            <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                          </td>
                          <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                            <div className="w-24 h-4 bg-gray-200 rounded"></div>
                          </td>
                          <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                            <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
                          </td>
                          <td className="px-3 sm:px-4 py-3 whitespace-nowrap">
                            <div className="w-20 h-4 bg-gray-200 rounded"></div>
                          </td>
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Development Testing Panel */}
          {process.env.NODE_ENV === 'development' && (
            <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🧪 Level System Testing (Dev Only)</h3>
              
              {/* Experience Testing */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Experience Testing</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  <button
                    onClick={() => handleTestAPI(() => api.user.test.addExperience(50))}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    +50 EXP
                  </button>
                  <button
                    onClick={() => handleTestAPI(() => api.user.test.addExperience(200))}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    +200 EXP
                  </button>
                  <button
                    onClick={() => handleTestAPI(() => api.user.test.addExperience(1000))}
                    className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    +1000 EXP
                  </button>
                  <button
                    onClick={() => handleViewLevelInfo()}
                    className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    View Level Info
                  </button>
                </div>
              </div>

              {/* Activity Testing */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Activity Testing</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  <button
                    onClick={() => handleTestAPI(() => api.user.test.simulateActivity())}
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    Simulate Activity
                  </button>
                  <button
                    onClick={() => {
                      clearActivityData();
                      alert('✅ Activity data cleared!');
                    }}
                    className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    Clear Activity
                  </button>
                  <button
                    onClick={saveActivityToBackend}
                    className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    Save to Server
                  </button>
                  <button
                    onClick={loadActivityFromBackend}
                    className="bg-cyan-500 hover:bg-cyan-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    Load from Server
                  </button>
                </div>
              </div>

              {/* General Testing */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">General Testing</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <button
                    onClick={() => handleTestAPI(() => api.user.test.resetStats())}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm transition-colors"
                  >
                    Reset All Stats
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}