'use client';

import BrandLogo from '@/components/common/BrandLogo';
import Avatar from '@/components/common/Avatar';
import { LogoutIcon } from '@/components/icons';

interface AvatarUser { name?: string; avatar_url?: string; avatarKey?: number }
interface NavBarAuthProps { user?: AvatarUser | null; onLogout?: () => void; showLogoutButton?: boolean }

export default function NavBarAuth({ user, onLogout, showLogoutButton = true }: NavBarAuthProps) {
  const avatarUser: AvatarUser = user || {};
  return (
    <nav data-global-nav className="fixed top-0 left-0 right-0 bg-white shadow-sm border-b w-full z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          <BrandLogo showText className="gap-2 sm:gap-3" size={36} />
          <div className="flex items-center gap-3 sm:gap-4">
            {user ? (
              <>
                <div className="hidden sm:flex items-center gap-3">
                  <Avatar user={avatarUser} size={40} className="w-8 h-8 sm:w-10 sm:h-10 border-2 border-gray-200" displayName={avatarUser.name || 'User'} showInitialsFallback cacheKey={avatarUser.avatarKey} />
                  <div className="hidden md:block">
                    <div className="text-sm text-gray-600">Xin chào,</div>
                    <div className="text-sm font-semibold text-gray-800 truncate max-w-32 lg:max-w-48">{avatarUser.name}</div>
                  </div>
                </div>
                <div className="sm:hidden">
                  <Avatar user={avatarUser} size={32} className="w-8 h-8 border-2 border-gray-200" displayName={avatarUser.name || 'User'} showInitialsFallback cacheKey={avatarUser.avatarKey} />
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3 sm:gap-4 animate-pulse">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gray-200" />
                <div className="hidden md:flex flex-col gap-1">
                  <div className="h-3 w-14 bg-gray-200 rounded" />
                  <div className="h-3 w-24 bg-gray-200 rounded" />
                </div>
              </div>
            )}
            {showLogoutButton && onLogout && user && (
              <button onClick={onLogout} className="flex items-center gap-1.5 bg-red-600 text-white px-3 py-2 sm:px-4 sm:py-2.5 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium">
                <LogoutIcon className="w-4 h-4" />
                <span className="hidden sm:inline">Đăng xuất</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
