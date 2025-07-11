'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { storage } from '@/utils/api';
import Avatar from '@/components/common/Avatar';
import {
  HomeIcon,
  BookOpenIcon,
  ClipboardListIcon,
  UserCircleIcon,
  LogoutIcon,
  PlusCircleIcon,
  DocumentTextIcon,
  MenuIcon,
} from '@/components/icons';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
  user?: {
    avatar_url?: string;
    name?: string;
    email?: string;
    avatarKey?: number;
  };
}

const menuItems = [
  { label: 'Trang Chủ', icon: HomeIcon, href: '/user/dashboard' },
  { label: 'Tạo Khóa Học', icon: PlusCircleIcon, href: '/user/create-course' },
  { label: 'Tạo Quiz', icon: DocumentTextIcon, href: '/user/create-quiz' },
  { label: 'Khóa Học', icon: BookOpenIcon, href: '/user/my-courses' },
  { label: 'Quiz', icon: ClipboardListIcon, href: '/user/my-quizzes' },
  { label: 'Hồ Sơ', icon: UserCircleIcon, href: '/user/profile' },
];

export default function Layout({ children, title, user }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      setSidebarOpen(!mobile);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLogout = () => {
    storage.removeToken();
    router.push('/auth/signin');
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 bg-gray-900 text-white transition-all duration-200
        ${isMobile ? (sidebarOpen ? 'w-64 translate-x-0' : 'w-64 -translate-x-full') : (sidebarOpen ? 'w-64' : 'w-16')}
      `}>
        {/* Logo */}
        <div className={`flex items-center h-14 px-3 border-b border-gray-700 ${!sidebarOpen && !isMobile && 'justify-center'}`}>
          <div className="flex items-center gap-2">
            <Image src="/assets/icons/logo.png" alt="logo" width={28} height={28} className="flex-shrink-0" />
            {(sidebarOpen || isMobile) && (
              <span className="font-bold text-lg">PathLight</span>
            )}
          </div>
        </div>

        {/* Menu */}
        <nav className="py-3 space-y-0.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => isMobile && setSidebarOpen(false)}
                className={`
                  flex items-center mx-2 px-3 py-2.5 rounded-lg transition-colors group
                  ${active ? 'bg-orange-500 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}
                  ${!sidebarOpen && !isMobile && 'justify-center mx-1'}
                `}
                title={!sidebarOpen && !isMobile ? item.label : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {(sidebarOpen || isMobile) && (
                  <span className="ml-3 font-medium">{item.label}</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="absolute bottom-3 left-0 right-0 px-2">
          <button
            onClick={handleLogout}
            className={`
              flex items-center w-full px-3 py-2.5 text-gray-300 hover:bg-red-600 hover:text-white rounded-lg transition-colors group
              ${!sidebarOpen && !isMobile && 'justify-center mx-1'}
            `}
            title={!sidebarOpen && !isMobile ? 'Đăng Xuất' : undefined}
          >
            <LogoutIcon className="w-5 h-5 flex-shrink-0" />
            {(sidebarOpen || isMobile) && (
              <span className="ml-3 font-medium">Đăng Xuất</span>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-3 sm:px-4 py-3 flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none"
              >
                <MenuIcon className="w-5 h-5" />
              </button>
            )}
            
            <div className="flex items-center gap-2">
              <Image 
                src="/assets/icons/logo.png" 
                alt="PathLight Logo" 
                width={24} 
                height={24} 
                className="w-6 h-6 object-contain lg:hidden"
              />
              <h1 className="text-lg font-semibold text-gray-900 truncate">{title}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Search */}
            <div className="hidden md:block relative">
              <input
                type="text"
                placeholder="Tìm kiếm..."
                className="w-40 lg:w-56 pl-8 pr-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm"
              />
              <svg className="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-1.5 p-1 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none"
              >
                <Avatar 
                  user={user || {}} 
                  size={28} 
                  className="w-7 h-7"
                  displayName={user?.name || user?.email || 'User'}
                  showInitialsFallback={true}
                />
                <div className="hidden sm:block text-left max-w-28 lg:max-w-36">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {user?.name || user?.email || 'User'}
                  </div>
                </div>
                <svg className="w-3 h-3 text-gray-400 hidden xs:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown */}
              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {user?.name || 'User'}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {user?.email || 'Email'}
                    </div>
                  </div>
                  <Link
                    href="/user/profile"
                    className="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    Hồ sơ của tôi
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogoutIcon className="w-4 h-4 mr-2" />
                    Đăng xuất
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
