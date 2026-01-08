'use client';

import { useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Leaderboard, LeaderboardTable } from '@/components/user/dashboard/Leaderboard';
import { useDashboard } from '@/components/user/dashboard/hooks';
import { Users, TrendingUp } from 'lucide-react';

export default function RankingPage() {
  const router = useRouter();
  const handleLogout = useCallback(() => router.push('/auth/login'), [router]);
  const { user, dashboardData, loading } = useDashboard(handleLogout);

  const users = dashboardData?.info?.user_top_rank || [];
  
  // Find competitors (user + 1 above + 1 below)
  const competitors = useMemo(() => {
    if (!user?.rank) return null;
    const currentIdx = users.findIndex(u => u.id === user.id);
    if (currentIdx === -1) return null;
    
    const above = currentIdx > 0 ? users[currentIdx - 1] : null;
    const below = currentIdx < users.length - 1 ? users[currentIdx + 1] : null;
    const current = users[currentIdx];
    
    const expGap = above ? (above.experience || 0) - (current.experience || 0) : 0;
    
    return { above, current, below, expGap };
  }, [users, user]);

  const expPercent = user?.require_exp 
    ? Math.min(100, Math.round(((user.current_exp || 0) / user.require_exp) * 100))
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-50 py-4 sm:py-6 md:py-8 px-3 sm:px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8 text-center">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-2">🏆 Bảng Xếp Hạng</h1>
          <p className="text-sm sm:text-base text-gray-600">Xem thứ hạng của bạn trong cộng đồng học tập</p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-lg shadow p-6 sm:p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
            <p className="mt-4 text-sm sm:text-base text-gray-600">Đang tải bảng xếp hạng...</p>
          </div>
        )}

        {/* Current User Stats Card */}
        {!loading && user && (
          <div className="mb-6 sm:mb-8 bg-gradient-to-br from-cyan-600 to-blue-700 rounded-2xl shadow-2xl p-4 sm:p-6 text-white">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
              {/* User Info */}
              <div className="md:col-span-1 flex flex-col items-center justify-center text-center md:border-r border-white/20 pb-4 md:pb-0">
                <div className="text-4xl sm:text-5xl md:text-6xl font-black mb-2">
                  #{user.rank || '—'}
                </div>
                <div className="text-xs sm:text-sm text-cyan-100">Thứ hạng của bạn</div>
                <div className="mt-2 sm:mt-3 text-xs text-cyan-200">
                  trong {user.total_users || 0} người dùng
                </div>
              </div>

              {/* Level & Exp Progress */}
              <div className="md:col-span-2 space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="text-center sm:text-left">
                    <h3 className="text-lg sm:text-xl font-bold">{user.name}</h3>
                    <p className="text-xs sm:text-sm text-cyan-100">{user.email}</p>
                  </div>
                  <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                    <div className="text-xl sm:text-2xl font-bold">Lv {user.level || 1}</div>
                    <div className="text-xs text-cyan-100">Level</div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs sm:text-sm">
                    <span>Tiến độ lên level</span>
                    <span className="font-semibold">{expPercent}%</span>
                  </div>
                  <div className="h-3 sm:h-4 bg-white/20 rounded-full overflow-hidden backdrop-blur-sm">
                    <div 
                      className="h-full bg-gradient-to-r from-yellow-400 via-amber-400 to-orange-400 transition-all duration-500 rounded-full shadow-lg"
                      style={{ width: `${expPercent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-cyan-100">
                    <span>{user.current_exp || 0} EXP</span>
                    <span>{user.require_exp || 0} EXP</span>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-2 sm:gap-3 pt-2">
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-3 text-center">
                    <div className="text-lg sm:text-xl font-bold">{user.completed_courses || 0}</div>
                    <div className="text-xs text-cyan-100">Khóa học</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-3 text-center">
                    <div className="text-lg sm:text-xl font-bold">{user.current_exp || 0}</div>
                    <div className="text-xs text-cyan-100">Kinh nghiệm</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-3 text-center">
                    <div className="text-lg sm:text-xl font-bold">{user.total_lessons || 0}</div>
                    <div className="text-xs text-cyan-100">Bài học</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Competitor Comparison Widget */}
        {!loading && competitors && (
          <div className="mb-4 sm:mb-6 bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl shadow-xl p-4 sm:p-6 border-2 border-orange-200">
            <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
              <Users className="w-5 h-5 sm:w-6 sm:h-6 text-orange-600" />
              <h3 className="text-lg sm:text-xl font-bold text-gray-900">Đối thủ xung quanh bạn</h3>
            </div>
            <div className="space-y-2 sm:space-y-3">
              {competitors.above && (
                <div className="bg-white rounded-lg p-3 sm:p-4 border-2 border-orange-200">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                      <div className="text-xl sm:text-2xl font-black text-orange-600 shrink-0">#{competitors.above.rank}</div>
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-gray-900 truncate text-sm sm:text-base">{competitors.above.name}</div>
                        <div className="text-xs sm:text-sm text-gray-600">Lv {competitors.above.level} • {(competitors.above.experience || 0).toLocaleString()} EXP</div>
                      </div>
                    </div>
                    <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-orange-500 shrink-0" />
                  </div>
                </div>
              )}
              <div className="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg p-3 sm:p-4 border-2 border-cyan-400 shadow-lg">
                <div className="flex items-center justify-between text-white gap-2">
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                    <div className="text-xl sm:text-2xl font-black shrink-0">#{competitors.current.rank}</div>
                    <div className="min-w-0 flex-1">
                      <div className="font-bold text-base sm:text-lg truncate">{competitors.current.name} (Bạn)</div>
                      <div className="text-xs sm:text-sm text-cyan-100">Lv {competitors.current.level} • {(competitors.current.experience || 0).toLocaleString()} EXP</div>
                    </div>
                  </div>
                </div>
              </div>
              {competitors.below && (
                <div className="bg-white rounded-lg p-3 sm:p-4 border-2 border-gray-200">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                      <div className="text-xl sm:text-2xl font-black text-gray-600 shrink-0">#{competitors.below.rank}</div>
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-gray-900 truncate text-sm sm:text-base">{competitors.below.name}</div>
                        <div className="text-xs sm:text-sm text-gray-600">Lv {competitors.below.level} • {(competitors.below.experience || 0).toLocaleString()} EXP</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            {competitors.above && competitors.expGap > 0 && (
              <div className="mt-3 sm:mt-4 bg-white rounded-lg p-3 sm:p-4 border-l-4 border-orange-500">
                <p className="text-xs sm:text-sm text-gray-700">
                  💪 <span className="font-semibold">Bạn chỉ còn cách {competitors.above.name} {competitors.expGap} EXP nữa thôi!</span> Học ngay 1 bài để vượt mặt nào!
                </p>
              </div>
            )}
          </div>
        )}

        {/* Ranking Display */}
        {!loading && users.length > 0 && (
          <div className="space-y-4 sm:space-y-6">
            {/* Top 3 Podium */}
            <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 md:p-8 border-2 border-amber-200">
              <div className="flex items-center justify-center gap-2 mb-4 sm:mb-6">
                <span className="text-2xl sm:text-3xl">👑</span>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Top 3 Xuất Sắc</h2>
              </div>
              <Leaderboard top={users} />
            </div>

            {/* Full Ranking Table */}
            <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 md:p-8">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4 mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">📊 Bảng Xếp Hạng</h2>
                <div className="text-xs sm:text-sm text-gray-500">
                  Tổng: <span className="font-semibold text-gray-900">{users.length}</span> người
                </div>
              </div>
              <LeaderboardTable users={users} currentUserId={user?.id} />
            </div>

            {/* Info Box */}
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl p-4 sm:p-6 border border-blue-200">
              <div className="flex items-start gap-3 sm:gap-4">
                <div className="text-2xl sm:text-3xl shrink-0">💡</div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">Cách tăng thứ hạng</h3>
                  <ul className="text-xs sm:text-sm text-gray-700 space-y-1">
                    <li>✅ Hoàn thành bài học và quiz để nhận EXP</li>
                    <li>🎯 Đạt điểm cao trong các bài kiểm tra</li>
                    <li>🔥 Duy trì streak học tập mỗi ngày</li>
                    <li>⚡ Tham gia thường xuyên để tích lũy kinh nghiệm</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && users.length === 0 && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-600">Chưa có dữ liệu bảng xếp hạng</p>
          </div>
        )}
      </div>
    </div>
  );
}
