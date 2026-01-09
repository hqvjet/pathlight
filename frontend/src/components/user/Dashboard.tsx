'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useActivity, useDashboard } from './dashboard/hooks';
import { ProfileCard } from './dashboard/ProfileCard';
import { ActivityHeatmap } from './dashboard/ActivityHeatmap';
import { userApi } from '@/lib/api/user';

interface DashboardProps {
  onLogout: () => void;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const { user, loading } = useDashboard(onLogout);
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

  const completionRate = user.total_courses > 0 
    ? Math.round((user.completed_courses / user.total_courses) * 100) 
    : 0;

  return (
    <div className="p-3 sm:p-4 md:p-6 lg:p-8 min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        
        {/* Header Row */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
          <div className="flex-1">
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900">
              Xin chào, {user.given_name || user.name}! 👋
            </h1>
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 mt-1">
              <p className="text-sm sm:text-base text-gray-600">
                {user.remind_time 
                  ? `Hẹn gặp bạn vào lúc ${user.remind_time} để học bài!` 
                  : 'Chào mừng trở lại hành trình học tập'}
              </p>
              <a 
                href="/user/profile" 
                className="text-xs text-blue-600 hover:text-blue-700 font-semibold hover:underline inline-block"
              >
                {user.remind_time ? 'Thay đổi giờ nhắc' : 'Cài đặt giờ nhắc'}
              </a>
            </div>
          </div>
          
          {/* Redesigned Streak - Responsive */}
          <div className="flex items-center gap-2">
            <svg 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="text-orange-500 w-6 h-6 sm:w-8 sm:h-8 drop-shadow-lg"
              style={{ 
                filter: (user?.streak ?? 0) > 10 ? 'drop-shadow(0 0 8px rgba(249, 115, 22, 0.5))' : 'none'
              }}
            >
              <path d="M12 2C12 2 8 6 8 10c0 2.21 1.79 4 4 4s4-1.79 4-4c0-4-4-8-4-8zm0 18c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.5 9.5C4.56 11.13 4 13 4 15c0 4.42 3.58 8 8 8s8-3.58 8-8c0-2-.56-3.87-1.5-5.5l-1.2 1.7c.45.83.7 1.79.7 2.8 0 3.31-2.69 6-6 6z"/>
            </svg>
            <div className="flex flex-col">
              <div className="flex items-baseline gap-1">
                <span className="text-2xl sm:text-3xl font-black text-orange-600">{user?.streak ?? 0}</span>
                <span className="text-xs sm:text-sm text-orange-600 font-bold">ngày</span>
              </div>
            </div>
          </div>
        </div>

        {/* Row 1: Profile & Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <ProfileCard user={user} />
          
          {/* Stats */}
          <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 border border-gray-200">
            <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-3 sm:mb-4">📊 Thống kê</h3>
            <div className="space-y-2 sm:space-y-3">
              <div className="flex items-center justify-between p-2 sm:p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-xl sm:text-2xl">📚</div>
                  <span className="text-xs sm:text-sm font-semibold text-gray-700">Khóa học</span>
                </div>
                <span className="text-lg sm:text-xl font-bold text-blue-600">{user.total_courses}</span>
              </div>
              <div className="flex items-center justify-between p-2 sm:p-3 bg-indigo-50 rounded-lg">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-xl sm:text-2xl">📖</div>
                  <span className="text-xs sm:text-sm font-semibold text-gray-700">Bài học</span>
                </div>
                <span className="text-lg sm:text-xl font-bold text-indigo-600">{user.total_lessons}</span>
              </div>
              <div className="flex items-center justify-between p-2 sm:p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-xl sm:text-2xl">📝</div>
                  <span className="text-xs sm:text-sm font-semibold text-gray-700">Quiz đã làm</span>
                </div>
                <span className="text-lg sm:text-xl font-bold text-purple-600">{user.completed_quizzes}</span>
              </div>
              <div className="flex items-center justify-between p-2 sm:p-3 bg-yellow-50 rounded-lg">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-xl sm:text-2xl">🏆</div>
                  <span className="text-xs sm:text-sm font-semibold text-gray-700">Xếp hạng</span>
                </div>
                <span className="text-lg sm:text-xl font-bold text-yellow-600">#{user.rank}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Row 2: Continue Learning & Top Learners */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Continue Learning */}
          <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 border-2 border-blue-200">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h3 className="text-lg sm:text-xl font-bold text-gray-900">🚀 Học tiếp</h3>
              <span className="text-xs sm:text-sm text-gray-600">Bài học đang học</span>
            </div>
            
            {user.total_courses > 0 ? (
              <div className="space-y-3 sm:space-y-4">
                {/* Main Course Card */}
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 sm:p-5 border border-blue-200">
                  <div className="flex items-center gap-3 sm:gap-4 mb-3 sm:mb-4">
                    <div className="w-12 h-12 sm:w-16 sm:h-16 bg-blue-500 rounded-lg flex items-center justify-center text-white text-xl sm:text-2xl shrink-0">
                      📚
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-gray-900 mb-1 text-sm sm:text-base">
                        Tiếp tục khóa học của bạn
                      </h4>
                      <p className="text-xs sm:text-sm text-gray-600">
                        Đã hoàn thành {user.completed_courses}/{user.total_courses} khóa học
                      </p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 sm:h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                            style={{ width: `${completionRate}%` }}
                          />
                        </div>
                        <span className="text-xs font-bold text-gray-600">{completionRate}%</span>
                      </div>
                    </div>
                  </div>
                  <Link 
                    href="/user/my-courses" 
                    className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 sm:py-3 rounded-lg transition-colors text-sm sm:text-base"
                  >
                    Xem khóa học của tôi →
                  </Link>
                </div>

                {/* Learning Progress Stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">📖</span>
                      <span className="text-sm font-semibold text-gray-700">Bài học</span>
                    </div>
                    <div className="text-2xl font-bold text-indigo-600">{user.total_lessons || 0}</div>
                    <p className="text-xs text-gray-600 mt-1">Tổng số bài học</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">📝</span>
                      <span className="text-sm font-semibold text-gray-700">Quiz</span>
                    </div>
                    <div className="text-2xl font-bold text-purple-600">{user.completed_quizzes || 0}</div>
                    <p className="text-xs text-gray-600 mt-1">Quiz đã làm</p>
                  </div>
                </div>

                {/* Motivational Quote */}
                <div className="bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl p-4 border-l-4 border-blue-500">
                  <p className="text-sm text-gray-700 italic">
                    💡 &ldquo;<span className="font-semibold">Học tập không bao giờ là lãng phí thời gian</span> - mỗi bài học đều mở ra cánh cửa tri thức mới!&rdquo;
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📚</div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Bắt đầu học ngay!</h4>
                <p className="text-sm text-gray-600 mb-6">
                  Bạn chưa đăng ký khóa học nào. Hãy khám phá và bắt đầu hành trình học tập.
                </p>
                <Link 
                  href="/user/my-courses" 
                  className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
                >
                  Khám phá khóa học
                </Link>
              </div>
            )}
          </div>

          {/* Top Learners */}
          <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-gray-900">🏆 Top Learners</h4>
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full font-semibold">
                  Top {Math.min(5, (user.user_top_rank || []).length)}
                </span>
              </div>
              <a href="/user/ranking" className="text-xs text-blue-600 hover:text-blue-700 hover:underline font-semibold">Xem tất cả →</a>
            </div>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {(user.user_top_rank || []).slice(0, 5).map((topUser, idx) => {
                const isCurrentUser = topUser.id === user.id;
                const medalIcon = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : null;
                return (
                  <div 
                    key={idx} 
                    className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                      isCurrentUser 
                        ? 'bg-gradient-to-r from-cyan-100 to-blue-100 border-2 border-cyan-300 shadow-sm' 
                        : idx < 3 
                          ? 'bg-gradient-to-r from-yellow-50 to-orange-50 hover:shadow-md' 
                          : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-10 h-10 bg-gradient-to-br ${
                      isCurrentUser 
                        ? 'from-cyan-500 to-blue-600' 
                        : idx < 3 
                          ? 'from-yellow-400 to-orange-500' 
                          : 'from-gray-400 to-gray-500'
                    } rounded-full flex items-center justify-center text-white text-sm font-bold shadow-md`}>
                      #{topUser.rank}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {medalIcon && <span className="text-lg">{medalIcon}</span>}
                        <div className={`text-sm font-semibold truncate ${
                          isCurrentUser ? 'text-cyan-900' : 'text-gray-900'
                        }`}>
                          {topUser.name} {isCurrentUser && '(Bạn)'}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-semibold">
                          Lv {topUser.level}
                        </span>
                        <span className="text-xs text-gray-600">{topUser.experience} EXP</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Row 3: Activity Heatmap */}
        <ActivityHeatmap
          selectedYear={selectedYear}
          setSelectedYear={setSelectedYear}
          generateYearActivityData={generateYearActivityData}
        />
      </div>
    </div>
  );
}