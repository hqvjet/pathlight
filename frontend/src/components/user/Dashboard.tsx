'use client';

import { useState, useMemo } from 'react';
import { useActivity, useDashboard } from './dashboard/hooks';
import Layout from '@/components/common/Layout';
import { UserProfile } from './dashboard/types';
import { StatsGrid } from './dashboard/StatsGrid';
import { ProfileCard } from './dashboard/ProfileCard';
import { ActivityHeatmap } from './dashboard/ActivityHeatmap';
import { Leaderboard, LeaderboardTable } from './dashboard/Leaderboard';

interface DashboardProps {
  onLogout: () => void;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const { user, dashboardData, loading } = useDashboard(onLogout);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const { handleActivityClick, generateYearActivityData } = useActivity();

  const layoutUser = useMemo(() => {
    if (!user) return { avatar_url: '', name: '', email: '' } as UserProfile;
    return { avatar_url: user.avatar_url || '', name: user.name, email: user.email, avatarKey: Date.now() } as UserProfile & { avatarKey: number };
  }, [user]);

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
    <Layout title="Trang Chủ" user={layoutUser}>
      <div className="p-4 sm:p-6 lg:p-8 min-h-screen">
        <div className="max-w-7xl mx-auto space-y-10">
          <StatsGrid user={user} />
          <div className="grid gap-6 md:grid-cols-3">
            <ProfileCard user={user} />
            <ActivityHeatmap selectedYear={selectedYear} setSelectedYear={setSelectedYear} generateYearActivityData={generateYearActivityData} handleActivityClick={handleActivityClick} />
          </div>
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold mb-6">Top Bảng Xếp Hạng</h3>
              <Leaderboard top={dashboardData?.info?.user_top_rank || []} />
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-6">Bảng Xếp Hạng Người Dùng</h3>
              <LeaderboardTable users={dashboardData?.info?.user_top_rank || []} />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}