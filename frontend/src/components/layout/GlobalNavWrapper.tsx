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

  if (pathname.startsWith('/user/')) return null;

  if (isAuthenticated) {
    // user?.name might be undefined until first profile fetch resolves; NavBarAuth shows skeleton then
    const avatarUser = user ? { name: user.name, avatar_url: user.avatar_url } : undefined;
    return <NavBarAuth user={avatarUser} onLogout={logout} />;
  }
  return <NavBarPublic />;
}
