'use client';

import { API_BASE, endpoints, storage } from '@/utils/api';

interface DashboardProps {
  onLogout: () => void;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const handleLogout = () => {
    storage.removeToken();
    onLogout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="text-2xl font-bold text-gray-900">🔥 PathLive</div>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Chào mừng bạn đến với PathLight</h2>
            <p className="text-gray-600">Bạn đã đăng nhập thành công vào hệ thống.</p>
            
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-blue-800">Khóa học</h3>
                <p className="text-blue-600 text-sm">Quản lý khóa học của bạn</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-semibold text-green-800">Bài kiểm tra</h3>
                <p className="text-green-600 text-sm">Tham gia bài kiểm tra</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="font-semibold text-purple-800">Tiến độ</h3>
                <p className="text-purple-600 text-sm">Theo dõi tiến độ học tập</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
