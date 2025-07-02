'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { API_BASE, storage } from '@/utils/api';
import { useRouter } from 'next/navigation';
import {
  HomeIcon,
  BookOpenIcon,
  ClipboardListIcon,
  UserCircleIcon,
  LogoutIcon,
  PlusCircleIcon,
  DocumentTextIcon,
  MenuIcon,
  ChevronLeftIcon,
} from '@/components/icons';
import Link from 'next/link';
import NavBar from '@/components/layout/NavBar';

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

const menuItems = [
  { label: 'Trang Chủ', icon: HomeIcon, href: '/dashboard' },
  { label: 'Tạo Khóa Học Mới', icon: PlusCircleIcon, href: '/dashboard/create-course' },
  { label: 'Tạo Quiz Mới', icon: DocumentTextIcon, href: '/dashboard/create-quiz' },
  { label: 'Khóa Học Của Tôi', icon: BookOpenIcon, href: '/dashboard/my-courses' },
  { label: 'Quiz Của Tôi', icon: ClipboardListIcon, href: '/dashboard/my-quizzes' },
  { label: 'Hồ Sơ Của Tôi', icon: UserCircleIcon, href: '/dashboard/profile' },
];

export default function Dashboard({ onLogout }: DashboardProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
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

  // Lấy pathname hiện tại để active menu
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';

  return (
    <div className="flex min-h-screen bg-gray-900">
      {/* Sidebar */}
      <aside
        className={`flex flex-col h-screen bg-gray-900 text-white transition-all duration-200 shadow-lg
          ${sidebarOpen ? 'w-64' : 'w-16'}
        `}
      >
        {/* Logo + Toggle */}
        <div className={`flex items-center h-16 px-4 border-b border-gray-800 
          ${sidebarOpen ? 'justify-between' : 'justify-center flex-col gap-2'}
        `}>
          {sidebarOpen ? (
            <>
              <div className="flex items-center gap-2">
                <Image 
                  src="/assets/icons/icon_logo.png" 
                  alt="logo" 
                  width={32} 
                  height={32} 
                  className="w-8 h-8 object-contain"
                />
                <span className="font-bold text-lg tracking-wide">PathLive</span>
              </div>
              <button
                className="text-gray-400 hover:text-white focus:outline-none"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle sidebar"
              >
                <ChevronLeftIcon size={20} />
              </button>
            </>
          ) : (
            <>
              <Image 
                src="/assets/icons/icon_logo.png" 
                alt="logo" 
                width={28} 
                height={28} 
                className="w-7 h-7 object-contain"
              />
              <button
                className="text-gray-400 hover:text-white focus:outline-none"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle sidebar"
              >
                <MenuIcon size={16} />
              </button>
            </>
          )}
        </div>
        {/* Menu */}
        <nav className="flex-1 py-4 flex flex-col gap-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = currentPath === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center transition-colors
                  ${active ? 'bg-orange-500 text-white' : 'hover:bg-gray-800 text-gray-200'}
                  ${sidebarOpen ? 'gap-3 px-4 py-3 justify-start' : 'justify-center px-2 py-3'}
                `}
                title={!sidebarOpen ? item.label : undefined}
              >
                <Icon className={`${sidebarOpen ? 'w-5 h-5' : 'w-5 h-5'}`} />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
        {/* Logout */}
        <div className={`mt-auto mb-4 ${sidebarOpen ? 'px-4' : 'px-2'}`}>
          <button
            onClick={handleLogout}
            className={`flex items-center w-full text-gray-400 hover:text-white rounded-lg transition-colors hover:bg-gray-800
              ${sidebarOpen ? 'gap-3 py-3 px-4 justify-start' : 'justify-center py-3 px-2'}
            `}
            title={!sidebarOpen ? 'Đăng Xuất' : undefined}
          >
            <LogoutIcon className="w-5 h-5" />
            {sidebarOpen && <span>Đăng Xuất</span>}
          </button>
        </div>
      </aside>
      {/* Main content */}
      <main className="flex-1 bg-white">
        <NavBar 
          user={user} 
          onLogout={handleLogout}
          showLogoutButton={false}
        />
        <div className="max-w-4xl mx-auto py-10 px-4">
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
                <Image 
                  src={user.avatar_url} 
                  alt="avatar" 
                  width={128} 
                  height={128} 
                  className="w-32 h-32 rounded-full object-cover border-4 border-blue-200 shadow-lg" 
                />
              )}
              <div className="text-lg font-semibold text-blue-800">{user.name}</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}