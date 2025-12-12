'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import NavBarPublic from '@/components/layout/NavBarPublic';
import NavBarAuth from '@/components/layout/NavBarAuth';
import { useAuthContext } from '@/context/AuthContext';

// This wrapper decides when to show the global top NavBar.
// We hide it on /user/* pages because those pages already have their own header/sidebar layout.
export default function GlobalNavWrapper() {
  const pathname = usePathname();
  const { isAuthenticated, user, logout } = useAuthContext();
  const [ready, setReady] = useState(false);

  useEffect(() => { setReady(true); }, []);

  if (!ready) return null; // avoid hydration mismatch

  // Hide global nav on dashboard-like pages and auth flows to avoid stale header flashes
  if (pathname.startsWith('/user/') || pathname.startsWith('/auth/')) return null;

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
}
