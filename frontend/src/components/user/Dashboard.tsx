'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { API_BASE, storage } from '@/utils/api';
import { useRouter } from 'next/navigation';

interface DashboardProps {
  onLogout: () => void;
}

interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  remind_time?: string;
  total_courses?: number;
  completed_courses?: number;
  total_quizzes?: number;
  average_score?: number;
  study_streak?: number;
  total_study_time?: number;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = storage.getToken();
        if (!token) throw new Error('No token');
        const res = await fetch(`${API_BASE}/api/v1/user/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
          setLoading(false);
          onLogout();
          return;
        }
        if (!res.ok) throw new Error('Failed to fetch profile');
        const data = await res.json();
        setUser(data);
        setLoading(false);
        if (!data.remind_time) {
          router.replace('/auth/study-time-setup');
        }
      } catch {
        setLoading(false);
        onLogout();
      }
    };
    fetchProfile();
    // eslint-disable-next-line
  }, []);

  const handleLogout = () => {
    storage.removeToken();
    onLogout();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500 animate-pulse">Đang tải thông tin...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-white">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              {user.avatar_url && (
                <Image src={user.avatar_url} alt="avatar" width={40} height={40} className="w-10 h-10" />
              )}
              <div>
                <div className="text-xl font-bold text-gray-900">🔥 PathLight</div>
                <div className="text-xs text-gray-500">Xin chào, <span className="font-semibold">{user.name}</span></div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors shadow"
            >
              Đăng xuất
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-10 px-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col md:flex-row gap-8 items-center">
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-blue-900 mb-2">Chào mừng bạn đến với PathLight!</h2>
            <p className="text-gray-700 mb-4">Bạn đã đăng nhập thành công vào hệ thống.</p>
            <ul className="grid grid-cols-2 gap-4 text-sm text-gray-700 mb-4">
              <li><span className="font-semibold">Email:</span> {user.email}</li>
              <li><span className="font-semibold">Thời gian nhắc học:</span> {user.remind_time || 'Chưa thiết lập'}</li>
              <li><span className="font-semibold">Tổng khóa học:</span> {user.total_courses ?? '—'}</li>
              <li><span className="font-semibold">Khóa học đã hoàn thành:</span> {user.completed_courses ?? '—'}</li>
              <li><span className="font-semibold">Tổng bài kiểm tra:</span> {user.total_quizzes ?? '—'}</li>
              <li><span className="font-semibold">Điểm TB:</span> {user.average_score ?? '—'}</li>
              <li><span className="font-semibold">Chuỗi ngày học:</span> {user.study_streak ?? '—'} ngày</li>
              <li><span className="font-semibold">Tổng thời gian học:</span> {user.total_study_time ?? '—'} phút</li>
            </ul>
          </div>
          <div className="flex flex-col items-center gap-4">
            {user.avatar_url && (
              <Image src={user.avatar_url} alt="avatar" width={128} height={128} className="w-32 h-32" />
            )}
            <div className="text-lg font-semibold text-blue-800">{user.name}</div>
          </div>
        </div>
      </main>
    </div>
  );
}