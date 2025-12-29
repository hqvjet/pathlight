'use client';

import { useEffect, useState } from 'react';
import { useActivity, useDashboard } from './dashboard/hooks';
import { StatsGrid } from './dashboard/StatsGrid';
import { ProfileCard } from './dashboard/ProfileCard';
import { ActivityHeatmap } from './dashboard/ActivityHeatmap';
import { Leaderboard, LeaderboardTable } from './dashboard/Leaderboard';
import { userApi } from '@/lib/api/user';

interface DashboardProps {
  onLogout: () => void;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const { user, dashboardData, loading } = useDashboard(onLogout);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const { generateYearActivityData } = useActivity();

  // Track login activity once per day
  useEffect(() => {
    const trackLoginActivity = async () => {
      const today = new Date().toDateString();
      const lastLoginDate = localStorage.getItem('lastLoginActivityDate');
      
      // Only track if it's a different day
      if (lastLoginDate !== today) {
        try {
          await userApi.logActivity('login');
          localStorage.setItem('lastLoginActivityDate', today);
        } catch (error) {
          // Silently fail if activity logging fails
          console.debug('Failed to log login activity:', error);
        }
      }
    };

    if (user?.id) {
      trackLoginActivity();
    }
  }, [user?.id]);

  // Ensure current user is in leaderboard
  const enhancedLeaderboard = () => {
    const topUsers = dashboardData?.info?.user_top_rank || [];
    if (!user?.id || !user?.rank) return topUsers;
    
    // Check if current user is already in the list
    const isInList = topUsers.some(u => u.id === user.id);
    if (isInList) return topUsers;
    
    // User not in top 10, inject them at their rank position
    const currentUserEntry = {
      rank: user.rank,
      name: user.name,
      level: user.level || 1,
      experience: user.current_exp || 0,
      avatar_url: user.avatar_url,
      id: user.id,
      initials: user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2),
      avatarKey: user.avatarKey
    };
    
    return [currentUserEntry, ...topUsers].slice(0, 10);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-lg text-gray-600 mb-2">Đang tải thông tin...</div>
          <div className="text-sm text-gray-400">Vui lòng đợi trong giây lát</div>
          <div className="mt-4 w-64 bg-gray-200 rounded-full h-2 mx-auto">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-lg text-gray-600 mb-4">Không tìm thấy thông tin người dùng</div>
          <button onClick={() => window.location.href = '/auth/login'} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors">Đăng nhập lại</button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-4 md:p-6 lg:p-8 min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8 lg:space-y-10">
        <StatsGrid user={user} />
        <div className="grid gap-4 sm:gap-6 md:grid-cols-3">
          <ProfileCard user={user} />
          <ActivityHeatmap
            selectedYear={selectedYear}
            setSelectedYear={setSelectedYear}
            generateYearActivityData={generateYearActivityData}
          />
        </div>
        <div className="grid gap-6 sm:gap-8 lg:grid-cols-2">
          <div>
            <h3 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-gray-800">Top Bảng Xếp Hạng</h3>
            <Leaderboard top={enhancedLeaderboard()} />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-gray-800">Bảng Xếp Hạng Người Dùng</h3>
            <LeaderboardTable users={enhancedLeaderboard()} />
          </div>
        </div>
      </div>
    </div>
  );
}