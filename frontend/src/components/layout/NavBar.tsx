'use client';

import Image from 'next/image';
import { LogoutIcon } from '@/components/icons';

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
    <nav className="bg-white shadow-sm border-b w-full">
      <div className="w-full px-8 xl:px-12">
        <div className="flex justify-between h-24 items-center">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <Image 
                src="/assets/icons/icon_logo.png" 
                alt="PathLight Logo" 
                width={48} 
                height={48} 
                className="w-12 h-12 object-contain" 
              />
              <div className="text-2xl font-bold text-gray-900">🔥 PathLight</div>
            </div>
            {user.avatar_url && (
              <div className="flex items-center gap-4 ml-6">
                <Image 
                  src={user.avatar_url} 
                  alt="avatar" 
                  width={56} 
                  height={56} 
                  className="w-14 h-14 rounded-full object-cover border-2 border-gray-200 shadow-sm" 
                />
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Xin chào,</span>
                  <span className="text-lg font-semibold text-gray-800">{user.name}</span>
                </div>
              </div>
            )}
          </div>
          
          {showLogoutButton && (
            <button
              onClick={onLogout}
              className="flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors shadow-md"
            >
              <LogoutIcon className="w-5 h-5" />
              <span>Đăng xuất</span>
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
