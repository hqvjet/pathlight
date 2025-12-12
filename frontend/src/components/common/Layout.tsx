'use client';

import { useState, useEffect } from 'react';
import { useAuthContext } from '@/context/AuthContext';
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
  MenuIcon,
} from '@/components/icons';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
  user?: {
    id?: string;
    avatar_url?: string;
    avatar_id?: string;
    google_avatar_url?: string;
    name?: string;
    email?: string;
    avatarKey?: number; // cache busting key
    level?: number;
    current_exp?: number;
    require_exp?: number;
    remind_time?: string;
    rank?: number;
  };
}

// Consolidated menu items
const menuItems = [
  { label: 'Trang Chủ', icon: HomeIcon, href: '/user/dashboard' },
  { label: 'Khóa Học Của Tôi', icon: BookOpenIcon, href: '/user/my-courses' },
  { label: 'Quiz Của Tôi', icon: ClipboardListIcon, href: '/user/my-quizzes' },
];

export default function Layout({ children, title, user }: LayoutProps) {
  const { user: ctxUser } = useAuthContext();
  // Prefer explicit user prop; fallback to context
  const effectiveUser = user || (ctxUser ? { id: ctxUser.id, name: ctxUser.name, email: ctxUser.email, avatar_url: ctxUser.avatar_url || (ctxUser.id ? `/api/users/avatar?user-id=${encodeURIComponent(ctxUser.id)}` : undefined), avatar_id: (ctxUser as { avatar_id?: string }).avatar_id, google_avatar_url: undefined, avatarKey: ctxUser.avatarKey, level: ctxUser.level, current_exp: ctxUser.current_exp, require_exp: ctxUser.require_exp, remind_time: ctxUser.remind_time, rank: ctxUser.rank } : undefined);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [cachedProgress, setCachedProgress] = useState<{ level?: number; current_exp?: number; require_exp?: number; rank?: number }>({});
  const [avatarVersion, setAvatarVersion] = useState<number | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const userMenuLinks = [
    { href: '/user/profile', label: 'Hồ sơ & tài khoản', sub: 'Cập nhật thông tin, ảnh đại diện' },
    { href: '/user/profile#remind', label: 'Nhắc giờ học', sub: 'Chỉnh thời gian thông báo hằng ngày' },
    { href: '/user/my-courses', label: 'Khóa học của tôi', sub: 'Xem lộ trình và tiến độ' },
  ];

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

  // Persist sidebar preference on desktop
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.localStorage?.getItem !== 'function') return;
    const stored = window.localStorage.getItem('pl_sidebar');
    if (stored && window.innerWidth >= 1024) {
      setSidebarOpen(stored === 'open');
    }
  }, []);
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.localStorage?.setItem !== 'function') return;
    if (window.innerWidth >= 1024) {
      window.localStorage.setItem('pl_sidebar', sidebarOpen ? 'open' : 'closed');
    }
  }, [sidebarOpen]);

  // Scroll shadow for header realism
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const cached = window.localStorage.getItem('pathlight_dashboard_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        const info = parsed?.dashboardData?.info || parsed?.user;
        if (info) {
          setCachedProgress({ level: info.level, current_exp: info.current_exp, require_exp: info.require_exp, rank: info.rank });
        }
      }
    } catch {
      /* ignore */
    }
  }, []);

  // Bust avatar cache whenever the user avatar changes
  useEffect(() => {
    setAvatarVersion(Date.now());
  }, [effectiveUser?.avatar_url, effectiveUser?.avatar_id, effectiveUser?.google_avatar_url]);

  const handleLogout = () => {
    storage.removeToken();
    router.push('/auth/signin');
  };

  const sidebarExpandedDesktop = !isMobile && sidebarOpen;
  const mainOffsetClasses = isMobile ? '' : sidebarExpandedDesktop ? 'lg:ml-64' : 'lg:ml-16';

  const expPercent = (() => {
    const current = effectiveUser?.current_exp ?? cachedProgress.current_exp ?? 0;
    const need = effectiveUser?.require_exp ?? cachedProgress.require_exp ?? 0;
    if (!need || need <= 0) return 0;
    const pct = current / need;
    return Math.max(0, Math.min(1, pct));
  })();

  const renderAvatarWithRing = () => {
    const ringSizeOuter = 46;
    const ringSizeInner = 40;
    const strokeOuter = 4;
    const strokeInner = 3;
    const radiusOuter = (ringSizeOuter - strokeOuter) / 2;
    const radiusInner = (ringSizeInner - strokeInner) / 2;
    const circInner = 2 * Math.PI * radiusInner;
    const dashInner = circInner * expPercent;
    const offsetInner = circInner - dashInner;
    return (
      <div className="relative" style={{ width: ringSizeOuter, height: ringSizeOuter }}>
        <svg className="absolute inset-0 -rotate-90" width={ringSizeOuter} height={ringSizeOuter}>
          <defs>
            <linearGradient id="xpOuter" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
            <linearGradient id="xpInner" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#2563eb" />
            </linearGradient>
          </defs>
          <circle cx={ringSizeOuter/2} cy={ringSizeOuter/2} r={radiusOuter} stroke="url(#xpOuter)" strokeWidth={strokeOuter} fill="none" opacity={0.35} />
          <circle cx={ringSizeOuter/2} cy={ringSizeOuter/2} r={radiusInner} stroke="rgba(0,0,0,0.08)" strokeWidth={strokeInner} fill="none" />
          <circle
            cx={ringSizeOuter/2}
            cy={ringSizeOuter/2}
            r={radiusInner}
            stroke="url(#xpInner)"
            strokeWidth={strokeInner}
            strokeLinecap="round"
            strokeDasharray={`${dashInner} ${circInner}`}
            strokeDashoffset={offsetInner}
            fill="none"
          />
        </svg>
        <div className="absolute inset-[7px] flex items-center justify-center rounded-full bg-white shadow-sm">
          <Avatar
            user={effectiveUser || {}}
            size={ringSizeInner - 10}
            className="w-8 h-8"
            displayName={effectiveUser?.name || effectiveUser?.email || 'User'}
            showInitialsFallback={true}
            cacheKey={effectiveUser?.avatarKey ?? avatarVersion ?? undefined}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar (always fixed so it doesn't stretch with content) */}
      <aside
        className={`group/sidebar fixed top-0 left-0 z-50 bg-gray-900 text-white flex flex-col h-screen transition-[width,transform] duration-200
        ${isMobile ? (sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full w-64') : (sidebarOpen ? 'w-64' : 'w-16')}`}
        data-collapsed={!sidebarOpen && !isMobile}
      >
        {/* Logo & Desktop Toggle */}
        <div className={`flex items-center h-14 px-3 border-b border-gray-700 ${!sidebarOpen && !isMobile && 'justify-center'}`}>
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <Image src="/assets/icons/logo.png" alt="logo" width={28} height={28} className="flex-shrink-0" />
            {(sidebarOpen || isMobile) && (
              <span className="font-bold text-lg truncate">PathLight</span>
            )}
          </div>
          {/* Desktop collapse toggle */}
          {!isMobile && (
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label={sidebarOpen ? 'Thu gọn sidebar' : 'Mở rộng sidebar'}
              className={`p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors ml-2 ${!sidebarOpen && 'rotate-180'}`}
            >
              <svg
                className="w-5 h-5 transition-transform"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
        </div>
        {/* Scrollable nav area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-700/60">
          <nav className="py-3 space-y-0.5">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => isMobile && setSidebarOpen(false)}
                  className={`flex items-center mx-2 px-3 py-2.5 rounded-lg transition-colors group focus:outline-none focus:ring-2 focus:ring-orange-500/60
                    ${active ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}
                    ${!sidebarOpen && !isMobile && 'justify-center mx-1'}`}
                  title={!sidebarOpen && !isMobile ? item.label : undefined}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {(sidebarOpen || isMobile) && <span className="ml-3 font-medium truncate">{item.label}</span>}
                </Link>
              );
            })}
          </nav>
        </div>
        {/* Logout */}
        <div className="px-2 pt-2 pb-3 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className={`flex items-center w-full px-3 py-2.5 text-gray-300 hover:bg-red-600/90 hover:text-white rounded-lg transition-colors group focus:outline-none focus:ring-2 focus:ring-red-500/60 ${!sidebarOpen && !isMobile && 'justify-center mx-1'}`}
            title={!sidebarOpen && !isMobile ? 'Đăng Xuất' : undefined}
          >
            <LogoutIcon className="w-5 h-5 flex-shrink-0" />
            {(sidebarOpen || isMobile) && <span className="ml-3 font-medium">Đăng Xuất</span>}
          </button>
        </div>
      </aside>

      {/* Main (adds left margin to account for fixed sidebar) */}
      <div className={`transition-all duration-200 ${mainOffsetClasses}`}>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className={`px-3 sm:px-4 h-14 sticky top-0 z-30 border-b transition-all bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/65 ${scrolled ? 'shadow-sm' : ''}`}>
            <div className="max-w-7xl mx-auto w-full h-full flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                {isMobile && (
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-1.5 rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-orange-500/60"
                    aria-label="Toggle menu"
                  >
                    <MenuIcon className="w-5 h-5" />
                  </button>
                )}
                <div className="flex items-center gap-2 min-w-0">
                  <Image src="/assets/icons/logo.png" alt="PathLight Logo" width={24} height={24} className="w-6 h-6 object-contain lg:hidden" />
                  <h1 className="text-base sm:text-lg font-semibold text-gray-900 truncate">{title}</h1>
                </div>
              </div>

              <div className="flex items-center gap-2 sm:gap-3">
                {/* Search */}
                <div className="hidden md:block relative">
                  <input
                    type="text"
                    placeholder="Tìm kiếm..."
                    className="w-40 lg:w-56 pl-8 pr-3 py-1.5 border border-gray-200 rounded-md bg-white/70 backdrop-blur focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm placeholder:text-gray-400"
                  />
                  <svg className="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                {/* User Menu */}
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className={`flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-orange-500/40 ${userMenuOpen ? 'bg-gray-100' : ''}`}
                  >
                    <div className="flex items-center gap-2">
                      {renderAvatarWithRing()}
                      <div className="flex flex-col leading-tight">
                        <div className="flex items-center gap-2 text-xs text-gray-600">
                          <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 font-semibold">Lv {effectiveUser?.level ?? cachedProgress.level ?? 1}</span>
                          <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold"># {effectiveUser?.rank ?? cachedProgress.rank ?? '—'}</span>
                        </div>
                        <div className="hidden sm:block text-left max-w-28 lg:max-w-36">
                          <div className="text-xs font-medium text-gray-500 leading-none truncate">{effectiveUser?.email || ''}</div>
                          <div className="text-sm font-semibold text-gray-900 truncate">{effectiveUser?.name || 'User'}</div>
                        </div>
                      </div>
                    </div>
                    <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 origin-top-right animate-in fade-in-0 zoom-in-95">
                      <div className="px-4 pb-2 mb-2 border-b border-gray-100">
                        <p className="text-sm font-semibold text-gray-900 truncate">{effectiveUser?.name || 'User'}</p>
                        <p className="text-xs text-gray-500 truncate">{effectiveUser?.email || 'Email'}</p>
                      </div>
                      <div className="py-1">
                        {userMenuLinks.map((item) => (
                          <Link
                            key={item.href}
                            href={item.href}
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                            onClick={() => setUserMenuOpen(false)}
                          >
                            <div className="font-medium text-gray-800">{item.label}</div>
                            {item.sub && <div className="text-xs text-gray-500">{item.sub}</div>}
                          </Link>
                        ))}
                      </div>
                      <button
                        onClick={handleLogout}
                        className="flex items-center w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogoutIcon className="w-4 h-4 mr-2" /> Đăng xuất
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </header>
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </div>
  );
}
