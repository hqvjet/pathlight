'use client';

import React, { useMemo } from 'react';
import Layout from '@/components/common/Layout';
import { useAuthContext } from '@/context/AuthContext';

interface UserSectionLayoutProps {
  children: React.ReactNode;
}

export default function UserSectionLayout({ children }: UserSectionLayoutProps) {
  // Derive the title from the current path (fallback generic)
  const title = '';

  const { user: authUser } = useAuthContext();
  const user = useMemo(() => {
    if (!authUser) return undefined;
    return {
      id: authUser.id,
      name: authUser.name,
      email: authUser.email,
      avatar_url: authUser.avatar_url,
      google_avatar_url: authUser.google_avatar_url,
      level: authUser.level,
      current_exp: authUser.current_exp,
      require_exp: authUser.require_exp,
      remind_time: authUser.remind_time,
      rank: authUser.rank,
    };
  }, [authUser]);

  return <Layout title={title} user={user}>{children}</Layout>;
}
