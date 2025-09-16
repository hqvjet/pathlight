'use client';

import Link from 'next/link';
import BrandLogo from '@/components/common/BrandLogo';
import { usePathname } from 'next/navigation';
import { useMemo, useEffect, useState } from 'react';

/**
 * NavBarPublic
 * Adaptive unauthenticated navigation that tailors CTA emphasis by context:
 *  - /auth/signin  -> Promote account creation (primary = Sign Up). Provide Home link (ghost)
 *  - /auth/signup  -> Emphasize Sign In for returning users (secondary) + Home (ghost)
 *  - Other pages   -> Show Sign In (secondary) + Sign Up (primary highlight)
 * Keeps surface intentionally minimal (brand + contextual actions) for focus & faster cognitive parsing.
 * Reusable utility 'btn' builds semantic variants to avoid style duplication.
 */

// Adaptive unauthenticated navbar
// - Signin page: primary action = Sign Up (emphasize conversion), offer subtle link back home
// - Signup page: primary action = Sign In
// - Other public pages: show both Sign In + Sign Up (highlight Sign Up)
// Keep surface minimal & focused: just brand + context actions
export default function NavBarPublic() {
  const pathname = usePathname();

  const context = useMemo(() => {
    if (pathname.startsWith('/auth/signin')) return 'signin';
    if (pathname.startsWith('/auth/signup')) return 'signup';
    return 'default';
  }, [pathname]);

  // Scroll-aware shrink for subtle polish
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const baseBtn = 'px-4 h-10 inline-flex items-center justify-center text-sm font-semibold rounded-md transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/60';

  // Small utility to assemble button classes by semantic variant
  const btn = (variant: 'primary' | 'secondary' | 'ghost', extra = '') => {
    const map: Record<string, string> = {
      primary: 'bg-orange-600 hover:bg-orange-700 text-white shadow-sm',
      secondary: 'border border-gray-300 bg-white hover:bg-gray-50 text-gray-700',
      ghost: 'border border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100'
    };
    return [baseBtn, map[variant], extra].filter(Boolean).join(' ');
  };

  const actions = () => {
    switch (context) {
      case 'signin':
        return (
          <div className="flex items-center gap-2 sm:gap-3">
            <Link href="/" className={btn('ghost')}>Trang Chủ</Link>
            <Link href="/auth/signup" className={btn('primary')}>Tạo Tài Khoản</Link>
          </div>
        );
      case 'signup':
        return (
          <div className="flex items-center gap-2 sm:gap-3">
            <Link href="/auth/signin" className={btn('secondary')}>Đăng Nhập</Link>
            <Link href="/" className={btn('ghost')}>Trang Chủ</Link>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 sm:gap-3">
            <Link href="/auth/signin" className={btn('secondary')}>Đăng Nhập</Link>
            <Link href="/auth/signup" className={btn('primary')}>Đăng Ký</Link>
          </div>
        );
    }
  };

  const tagline = () => {
    switch (context) {
      case 'signin':
        return 'Chào mừng trở lại — tiếp tục hành trình học tập';
      case 'signup':
        return 'Bắt đầu miễn phí chỉ với 60 giây';
      default:
        return 'Nền tảng học tập giúp bạn tiến bộ mỗi ngày';
    }
  };

  // Removed secondary inline navigation (about/courses/contact) per request to simplify header
  const subtleLinks = () => null;

  return (
    <nav
      data-global-nav
      className={`fixed top-0 left-0 right-0 z-50 border-b border-orange-100/70 backdrop-blur supports-[backdrop-filter]:bg-white/80 bg-white/90 transition-all ${scrolled ? 'shadow-sm' : ''}`}
    >
      {/* Thin gradient accent bar for brand energy */}
      <div className="h-0.5 bg-gradient-to-r from-orange-500 via-amber-400 to-rose-400" />
      <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`}>
        <div className={`flex items-center justify-between gap-6 ${scrolled ? 'h-14 sm:h-16' : 'h-16 sm:h-20'}`}>
          <div className="flex items-center gap-8 min-w-0 flex-1">
            <BrandLogo />
            {subtleLinks()}
            <span className="hidden xl:inline-flex text-sm text-gray-500 truncate max-w-xs 2xl:max-w-sm">{tagline()}</span>
          </div>
          <div className="flex items-center gap-4">
            {/* Trust badge only on default & signup for persuasion */}
            {(context === 'default' || context === 'signup') && (
              <div className="hidden md:flex items-center gap-1 text-[11px] font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Học viên mới mỗi ngày
              </div>
            )}
            {actions()}
          </div>
        </div>
      </div>
    </nav>
  );
}
