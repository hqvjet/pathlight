'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import NavBarPublic from '@/components/layout/NavBarPublic';
import NavBarAuth from '@/components/layout/NavBarAuth';
import { useAuthContext } from '@/context/AuthContext';

// This wrapper decides when to show the global top NavBar.
// We hide it on /user/* and /admin/* pages because those pages have their own layouts.
export default function GlobalNavWrapper() {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => { setReady(true); }, []);

  if (!ready) return null; // avoid hydration mismatch

  // Hide global nav on dashboard-like pages and admin pages
  if (pathname.startsWith('/user/')) return null;
  if (pathname.startsWith('/admin')) return null;
  if (pathname.startsWith('/auth/')) return <NavBarPublic />;

  // For other routes, use AuthContext (will be available via ConditionalAuthProvider)
  try {
    const { isAuthenticated, user, logout } = useAuthContext();
    
    if (isAuthenticated) {
      // user?.name might be undefined until first profile fetch resolves; NavBarAuth shows skeleton then
      const avatarUser = user
        ? {
            id: user.id,
            name: user.name,
            avatar_url: user.avatar_url,
            google_avatar_url: user.google_avatar_url,
            avatarKey: (user as { avatarKey?: number }).avatarKey,
            rank: (user as { rank?: number }).rank,
          }
        : undefined;
      return <NavBarAuth user={avatarUser} onLogout={logout} />;
    }
    return <NavBarPublic />;
  } catch (e) {
    // If AuthContext not available (shouldn't happen with ConditionalAuthProvider), show public nav
    return <NavBarPublic />;
  }
}
