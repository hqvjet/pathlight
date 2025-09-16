'use client';

import { usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useEffect, useState } from 'react';
import NavBarPublic from '@/components/layout/NavBarPublic';
import NavBarAuth from '@/components/layout/NavBarAuth';

// This wrapper decides when to show the global top NavBar.
// We hide it on /user/* pages because those pages already have their own header/sidebar layout.
export default function GlobalNavWrapper() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => { setReady(true); }, []);
  if (!ready) return null; // avoid hydration mismatch

  if (pathname.startsWith('/user/')) return null;

  if (isAuthenticated) {
    return <NavBarAuth user={{ name: 'Người Dùng' }} onLogout={logout} />;
  }
  return <NavBarPublic />;
}
