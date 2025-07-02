'use client';

import { useEffect, useState } from 'react';
import { API_BASE, storage } from '@/utils/api';
import UserLayout from '@/components/layout/UserLayout';

interface UserProfilePageProps {
  onLogout: () => void;
}

export default function UserProfilePage({ onLogout }: UserProfilePageProps) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
      } catch {
        setLoading(false);
        onLogout();
      }
    };
    fetchProfile();
    // eslint-disable-next-line
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500 animate-pulse">Đang tải thông tin...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <UserLayout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Hồ Sơ Của Tôi</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Thông tin cơ bản</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tên</label>
                  <p className="text-gray-900">{user.name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Thời gian nhắc học</label>
                  <p className="text-gray-900">{user.remind_time || 'Chưa thiết lập'}</p>
                </div>
              </div>
            </div>
            
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Thống kê học tập</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tổng khóa học</label>
                  <p className="text-gray-900">{user.total_courses ?? '—'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Khóa học đã hoàn thành</label>
                  <p className="text-gray-900">{user.completed_courses ?? '—'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Điểm trung bình</label>
                  <p className="text-gray-900">{user.average_score ?? '—'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Chuỗi ngày học</label>
                  <p className="text-gray-900">{user.study_streak ?? '—'} ngày</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UserLayout>
  );
}
