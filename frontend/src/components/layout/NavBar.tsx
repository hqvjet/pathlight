'use client';

import Image from 'next/image';
import { LogoutIcon } from '@/components/icons';
import Avatar from '@/components/common/Avatar';

interface NavBarProps {
  user: {
    name: string;
    avatar_url?: string;
  };
  onLogout: () => void;
  showLogoutButton?: boolean;
}

export default function NavBar({ user, onLogout, showLogoutButton = false }: NavBarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm border-b w-full z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          {/* Logo */}
          <div className="flex items-center gap-2 sm:gap-3">
            <Image 
              src="/assets/icons/icon_logo.png" 
              alt="PathLight Logo" 
              width={36} 
              height={36} 
              className="w-8 h-8 sm:w-9 sm:h-9 object-contain" 
            />
            <div className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900">PathLight</div>
          </div>

          {/* User Info (only show if user exists) */}
          {user && (
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="hidden sm:flex items-center gap-3">
                <Avatar 
                  user={user} 
                  size={40} 
                  className="w-8 h-8 sm:w-10 sm:h-10 border-2 border-gray-200"
                  displayName={user?.name || 'User'}
                  showInitialsFallback={true}
                />
                <div className="hidden md:block">
                  <div className="text-sm text-gray-600">Xin chào,</div>
                  <div className="text-sm font-semibold text-gray-800 truncate max-w-32 lg:max-w-48">
                    {user.name}
                  </div>
                </div>
              </div>
              
              {/* Mobile Avatar */}
              <div className="sm:hidden">
                <Avatar 
                  user={user} 
                  size={32} 
                  className="w-8 h-8 border-2 border-gray-200"
                  displayName={user?.name || 'User'}
                  showInitialsFallback={true}
                />
              </div>
              
              {showLogoutButton && (
                <button
                  onClick={onLogout}
                  className="flex items-center gap-1.5 bg-red-600 text-white px-3 py-2 sm:px-4 sm:py-2.5 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                >
                  <LogoutIcon className="w-4 h-4" />
                  <span className="hidden sm:inline">Đăng xuất</span>
                </button>
              )}
            </div>
          )}
          
          {/* No user - show nothing or login button */}
          {!user && showLogoutButton && (
            <div className="flex items-center">
              <button
                onClick={onLogout}
                className="flex items-center gap-1.5 bg-orange-600 text-white px-3 py-2 sm:px-4 sm:py-2.5 rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium"
              >
                <span>Đăng nhập</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
